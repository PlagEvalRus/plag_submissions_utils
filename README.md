

# Установка #
Установка производится с помощью утилиты ansible.
Поддерживаются операционные системы Debian 8  и Ubunut 16.04

Установка ansible:
```bash
sudo apt-get install libffi-dev python-dev libssl-dev sshpass python-pip
sudo pip install -U pyasn1 netaddr ansible==2.1.2
```

TODO - выкачать из гит
Установить зависимости ansible
```bash
cd plag_submissions_checker
sudo ansible-galaxy install -r ansible/requirements.yml
```
Запусить процесс настройки программы.
```bash
bash ./setup_localhost.sh
```
**Внимание**: в ходе установки и настройки будет сконфигурирован  веб-сервер apache,
при этом будет удалена дефолтная конфигурация из папки sites-enabled.
Дефолтная конфигурация останется в директории sites-available.

#  Установка в виртуальной машине #
Поддерживается установка в виртуальной машине с использованием Vagrant.
Для этого нужно [установить](https://www.vagrantup.com/docs/installation/) Vagrant.
И запустить в папке проекта:
```bash
vagrant up
```
Чтобы узнать адрес виртуальной машины выполните команду:
```bash
vagrant ssh-config
```
Чтобы залогиниться в виртуальную машину выполните:
```bash
vagrant ssh
```


# Возможные проблемы при установке #

Если возникает ошибка:
`OSError: [Errno 13] Permission denied: '/home/plagevaluser/.ansible/tmp'`

нужно выполнить команду:
```bash
sudo chown -R <user>:<user> ~/.ansible 
```
заменив `<user>` на имя актуального пользователя.

-------------------------------------------------------------------------------

