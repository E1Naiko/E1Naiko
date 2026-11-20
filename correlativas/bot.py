"""Comandos de correlativas independientes del transporte de chat."""
import argparse
import json
import os
import re
import sqlite3
from pathlib import Path


class Bot:
    def __init__(self, db, admins=None):
        if admins is None:
            admins = os.environ.get("BOT_ADMIN_IDS", "").split(",")
        self.admins = {str(a).strip() for a in admins if str(a).strip()}
        self.db = db
        self.base = {p.stem: json.loads(p.read_text(encoding='utf8'))
                       for p in Path(__file__).with_name('planes').glob('*.json')}
        db.executescript('''
            CREATE TABLE IF NOT EXISTS planes_admin(plan TEXT PRIMARY KEY);
            CREATE TABLE IF NOT EXISTS materias_admin(plan TEXT, codigo TEXT, nombre TEXT NOT NULL,
                anio INTEGER NOT NULL, previas TEXT NOT NULL, PRIMARY KEY(plan, codigo));
            CREATE TABLE IF NOT EXISTS usuarios(usuario TEXT PRIMARY KEY, plan TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS aprobadas(usuario TEXT, plan TEXT, codigo TEXT,
                PRIMARY KEY(usuario, plan, codigo));
        ''')

    def catalogo(self):
        planes = {plan: materias.copy() for plan, materias in self.base.items()}
        for plan, in self.db.execute('SELECT plan FROM planes_admin'):
            planes.setdefault(plan, {})
        for plan, codigo, nombre, anio, previas in self.db.execute(
                'SELECT plan, codigo, nombre, anio, previas FROM materias_admin'):
            planes[plan][codigo] = dict(nombre=nombre, anio=anio, previas=json.loads(previas))
        return planes

    def administrar(self, texto, planes):
        uso = ('admin agregar plan <plan> | admin agregar materia <plan> <código> '
               '<año> <nombre> [| previa1,previa2]')
        partes = texto.split(maxsplit=3)
        if len(partes) != 4 or partes[1].casefold() != 'agregar':
            return uso
        tipo, argumentos = partes[2].casefold(), partes[3]
        if tipo == 'plan':
            plan = argumentos.casefold()
            if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', plan):
                return 'Usá un identificador con letras, números y guiones, sin espacios.'
            if plan in planes:
                return 'El plan ya existe.'
            with self.db:
                alta = self.db.execute('INSERT OR IGNORE INTO planes_admin VALUES (?)', (plan,))
            return 'Plan agregado: ' + plan if alta.rowcount else 'El plan ya existe.'
        if tipo != 'materia':
            return uso
        datos = argumentos.split(maxsplit=3)
        if len(datos) != 4:
            return uso
        plan, codigo, anio, detalle = datos
        plan, codigo = plan.casefold(), codigo.upper()
        if plan not in planes:
            return 'El plan no existe.'
        if not re.fullmatch(r'[A-Z0-9]+(?:-[A-Z0-9]+)*', codigo) or not re.fullmatch(r'[1-9][0-9]?', anio):
            return 'Código inválido o año fuera del rango 1–99.'
        existentes = {k.casefold(): k for k in planes[plan]}
        if codigo.casefold() in existentes:
            return 'El código ya existe en el plan.'
        nombre, separador, lista = detalle.partition('|')
        nombre = nombre.strip()
        if not nombre:
            return uso
        requisitos = []
        if separador:
            for previa in lista.split(','):
                clave = previa.strip().casefold()
                if clave not in existentes:
                    return 'Cada previa debe ser una materia existente del mismo plan.'
                requisitos.append({'codigo': existentes[clave]})
        with self.db:
            alta = self.db.execute('INSERT OR IGNORE INTO materias_admin VALUES (?, ?, ?, ?, ?)',
                                   (plan, codigo, nombre, int(anio), json.dumps([requisitos] if requisitos else [])))
        return 'Materia agregada: ' + nombre if alta.rowcount else 'El código ya existe en el plan.'

    def responder(self, usuario, mensaje):
        palabras = mensaje.strip().lstrip('/').casefold().split()
        catalogo = self.catalogo()
        if palabras[:1] == ['admin']:
            if str(usuario) not in self.admins:
                return 'Comando reservado a administradores.'
            return self.administrar(mensaje.strip().lstrip('/'), catalogo)
        planes = 'Planes: ' + ', '.join(sorted(catalogo))
        if palabras[:1] == ['unirse'] and len(palabras) == 2:
            plan = palabras[1]
            if plan not in catalogo:
                return planes
            with self.db:
                self.db.execute('INSERT OR REPLACE INTO usuarios VALUES (?, ?)', (usuario, plan))
            return 'Plan activo: ' + plan
        if palabras[:2] in (['mostrar', 'anio'], ['mostrar', 'año']) and len(palabras) == 4:
            plan, anio = palabras[2:]
            if plan not in catalogo:
                return planes
            if not re.fullmatch('[1-9][0-9]*', anio):
                return 'Ingresá un año positivo.'
            return listado(catalogo[plan], lambda k, m: str(m['anio']) == anio)
        aprobar = palabras[:2] == ['aprobar', 'materia'] and len(palabras) >= 3
        if not aprobar and palabras != ['materias', 'quiensigue']:
            return ('unirse <plan> | aprobar materia <código o nombre> | mostrar anio <plan> <número> '
                    '| materias quiensigue\n' + planes)
        fila = self.db.execute('SELECT plan FROM usuarios WHERE usuario=?', (usuario,)).fetchone()
        if not fila:
            return 'Primero usá unirse <plan>. ' + planes
        plan, = fila
        materias = catalogo[plan]
        if aprobar:
            consulta = ' '.join(palabras[2:])
            opciones = [k for k, m in materias.items() if consulta in (k.casefold(), m['nombre'].casefold())]
            if len(opciones) != 1:
                return 'No se identificó una materia única. Usá el código del plan.'
            codigo, = opciones
            with self.db:
                alta = self.db.execute('INSERT OR IGNORE INTO aprobadas VALUES (?, ?, ?)',
                                       (usuario, plan, codigo)).rowcount
            return ('Aprobada: ' if alta else 'Ya estaba aprobada: ') + materias[codigo]['nombre']
        hechas = {k for k, in self.db.execute('SELECT codigo FROM aprobadas WHERE usuario=? AND plan=?',
                                              (usuario, plan))}
        return listado(materias, lambda k, m: k not in hechas and (not m['previas'] or any(
            all(cumple(r, hechas) for r in opcion) for opcion in m['previas'])))


def cumple(requisito, hechas):
    if 'codigo' in requisito:
        return requisito['codigo'] in hechas
    cantidad = re.fullmatch(r'Tener (\d+) actividades', requisito.get('especial', ''))
    return bool(cantidad and len(hechas) >= int(cantidad[1]))


def listado(materias, incluir):
    return '\n'.join(f"{k} · {m['nombre']}" for k, m in materias.items() if incluir(k, m)) or 'No hay materias.'


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('usuario')
    parser.add_argument('mensaje', nargs='+')
    args = parser.parse_args()
    with sqlite3.connect('progreso.sqlite3') as db:
        print(Bot(db).responder(args.usuario, ' '.join(args.mensaje)))
