# fix_imghdr.py
import sys
import types

# Создаем фиктивный модуль imghdr для Python 3.13+
def create_fake_imghdr():
    fake_imghdr = types.ModuleType('imghdr')
    
    def what(file, h=None):
        return None
    
    fake_imghdr.what = what
    sys.modules['imghdr'] = fake_imghdr
    print("✅ Фиктивный модуль imghdr создан")

# Применяем фикс
create_fake_imghdr()
