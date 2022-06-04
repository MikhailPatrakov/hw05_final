# Социальная сеть YaTube с использованием фреймворка Django.

Социальная сеть с возможностью создания, просмотра, редактирования и удаления записей, добавления изображений, а также реализован механизмом подписки на авторов. Проект покрыт тестами. Оформление выполнено на базе собственных шаблонов и подключен bootstrap.

* Инструментарий:
  * Django 2.2
  * Python 3.7
  * Django Unittest
  * Django ORM

* Как запустить проект:
  * Клонировать репозиторий:
    * `git clone https://github.com/MikhailPatrakov/hw05_final.git`
  * Установить зависимости:
    * `pip install -r requirements.txt`
  * Примененить миграций:
    * `python manage.py migrate`
  * Создать администратора:
    * `python manage.py createsuperuser`
  * Запустить приложение:
    * `python manage.py runserver`