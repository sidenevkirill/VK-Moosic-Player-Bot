# fix_imghdr.py
import sys
import types

# Создаем фиктивный модуль imghdr
class FakeImghdr:
    @staticmethod
    def what(file, h=None):
        return None

# Добавляем фиктивный модуль в sys.modules
sys.modules['imghdr'] = types.ModuleType('imghdr')
sys.modules['imghdr'].what = FakeImghdr.what