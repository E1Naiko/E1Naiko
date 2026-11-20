import sqlite3
import unittest
from correlativas.bot import Bot


class Comandos(unittest.TestCase):
    def test_progreso_independiente(self):
        db = sqlite3.connect(':memory:')
        responder = Bot(db).responder
        for usuario in ('ana', 'juan'):
            responder(usuario, 'unirse computacion-2024')
        self.assertIn('F1301', responder('ana', 'mostrar anio computacion-2024 1'))
        responder('ana', 'aprobar materia D1001')
        self.assertIn('Ya estaba', responder('ana', 'aprobar materia D1001'))
        siguientes = Bot(db).responder('ana', 'materias quiensigue')
        self.assertIn('F1301', siguientes)
        self.assertNotIn('D1001', siguientes)
        self.assertNotIn('F1301', responder('juan', 'materias quiensigue'))
        db.close()

    def test_admin(self):
        db = sqlite3.connect(':memory:')
        self.addCleanup(db.close)
        cmd = Bot(db, admins={'42'}).responder
        plan = 'admin agregar plan sistemas'
        self.assertIn('reservado', cmd('ana', plan))
        self.assertIn('agregado', cmd('42', plan))
        self.assertIn('existe', cmd('42', plan))
        materia = 'admin agregar materia sistemas M1 1 Matemática I'
        self.assertIn('reservado', cmd('ana', materia))
        self.assertIn('agregada', cmd('42', materia))
        self.assertIn('existe', cmd('42', materia))
        otra = 'admin agregar materia sistemas M2 2 Matemática II | '
        self.assertIn('previa', cmd('42', otra + 'NO'))
        self.assertIn('agregada', cmd('42', otra + 'M1'))
        cmd = Bot(db, admins=[]).responder
        cmd('ana', 'unirse sistemas')
        self.assertIn('Matemática II', cmd('ana', 'mostrar anio sistemas 2'))
        self.assertNotIn('M2', cmd('ana', 'materias quiensigue'))
        cmd('ana', 'aprobar materia M1')
        self.assertIn('M2', cmd('ana', 'materias quiensigue'))
