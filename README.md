# hydra-engine
* [Описание файла с метаданными для конфигурационного файла](#описание-файла-с-метаданными-для-конфигурационного-файла)
    * [Пример структуры файла](#пример-структуры-файла)
        * [FILE](#file)
            * [type](#type)
            * [path](#path)
        * [PARAMS](#params)
* [Описание метаданных для параметров конфигурационных файлов](#описание-метаданных-для-параметров-конфигурационных-файлов)
    * [type](#type-1)
    * [sub_type](#sub_type)
    * [sub_type_schema](#sub_type_schema)
    * [readonly](#readonly) 
    * [additional](#additional)
    * [id](#id)
    * [render](#render)
        * [control](#control)
        * [display_name](#display_name)
        * [constraints](#constraints)
* [Описание метаданных в файлах навигации](#описание-метаданных-в-файлах-навигацииwizardmetauimeta)
    * [Структура файла](#структура-файла)
    * [Описание полей](#описание-полей)
## Описание файла с метаданными для конфигурационного файла
Файл имеет расширение .meta. К примеру, common.yml.meta
### Пример структуры файла
```yaml
FILE:
  type: 'yaml'
  path: 'common.yml'

PARAMS:
    - site_name:
        type: string
        default_value: "site"
        sub_type: # optional for array
        sub_type_schema:
        readonly: False
        description: ""
        id: 5
        render:
          control: input_control
          display_name: "Site name"
          constraints:
```
#### FILE
Здесь описывается взаимосвязь между конфигурационном файлом и файлом с метаданными
##### type
Тип конфигурационного файла
##### path
Имя конфигурационного файла(должны находиться на одном уровне в одной папке)
#### PARAMS
Список с метаданными параметров конфигурационного файла
## Описание метаданных для параметров конфигурационных файлов

| Поле                                | Описание                             | Обязательно заполнить                           |
|-------------------------------------|--------------------------------------|-------------------------------------------------|
| [type](#type-1)                     | Тип данных параметра                 | Да                                              |
| default_value                       | Плейсхолдер                          | Нет                                             |
| [sub_type](#sub_type)               | Поле для указания типа данных для массива | Только для массива                              |
| [sub_type_schema](#sub_type_schema) | Поле для указания схемы словаря или массива объектов | Только для словаря и массива объектов           |
| [readonly](#readonly)               | Право для редактирования             | Да                                              |
| [additional](#additional)           | Дополнительное поле                  | Нет                                             |
| description                         | Описание параметра                   | Нет                                             |
| [id](#id)                           | Идентификатор формы к которому принадлежит параметр | Только для первого уровня вложенности параметра |
| [render](#render)                   | Данные для рендеринга параметра в ui | Да                                              |

### type
Ниже представлены все возможные типы для параметров.
* string
* string-single-quoted 
* string-double-quoted 
* int 
* bool 
* datetime 
* dict 
* array 
* double

### sub_type
* string
* string-single-quoted 
* string-double-quoted 
* int 
* bool 
* datetime
* composite(для массива объектов) 
* double

### sub_type_schema
В данном поле описывается схема для словаря или массива объектов
Формат описания схемы совпадает с форматом описания метаданных параметра.

Ниже указан пример для параметра dns.

```yaml
dns:
  recursors:
    - "10.74.10.21"
    - "10.74.10.22"
    - "10.74.10.23"
    - "10.74.10.24"
    - "10.74.10.25"
  forwarded_zones: 
    - name: ccfa-stage-pc.consul
      ips: 
        - 127.0.0.1
```
Метаданные параметра
```yaml
- dns:
        type: dict
        default_value:
        sub_type:
        sub_type_schema:
          recursors:
            type: array
            default_value:
            sub_type: string-double-quoted
            sub_type_schema:
            readonly: False
            description: ""
            render:
              control: input_control
              display_name: "Recursors"
              constraints:
          forwarded_zones:
            type: array
            default_value:
            sub_type: composite
            sub_type_schema:
              name:
                type: string
                default_value: "name"
                sub_type: # optional for array
                sub_type_schema:
                readonly: False
                description: ""
                render:
                  control: input_control
                  display_name: "Name"
                  constraints:
              ips:
                type: array
                default_value:
                sub_type: string
                sub_type_schema:
                readonly: False
                additional: True
                description: ""
                render:
                  control: input_control
                  display_name: "Ips"
                  constraints:
            readonly: False
            description: ""
            render:
              control: label_control
              display_name: "Forwarded zones"
              constraints:
        description: ""
        id: 5
        render:
          control: label_control
          display_name: "Dns"
          constraints:
```

### readonly
True - только чтение

False - редактирование, добавление и удаление элементов(массив)

#### Примечание
Если нужно для определенного поля в массиве объектов указать readonly: True, то надо написать в следующем формате:

```
readonly:
    №: True
```
№ - номер элемента массива(считаем с 1)
##### Пример
```yaml
users_dict:
    default_value:
    type: array
    sub_type: composite
    sub_type_schema:
      username:
        type: string-double-quoted
        default_value: ""
        sub_type:
        sub_type_schema:
        readonly:
          1: True
        description: ""
        render:
          control: input_control
          display_name: "User name"
          constraints:
      ssh_key:
        type: string-double-quoted
        default_value: ""
        sub_type:
        sub_type_schema:
        readonly: False
        description: ""
        render:
          control: textarea_control
          display_name: "Ssh key"
          constraints:
      sudoers:
        type: string
        default_value: "no"
        sub_type:
        sub_type_schema:
        readonly:
          1: True
        additional: True
        description: ""
        render:
          control: input_control
          display_name: "Sudoers"
          constraints:
            - pattern:
                value: "^(yes|no)$"
                message: "Valid values: yes, no"
      noPassSudo:
        type: string
        default_value: no
        sub_type:
        sub_type_schema:
        readonly:
          1: True
        additional: True
        description: ""
        render:
          control: input_control
          display_name: "NoPassSudo"
          constraints:
            - pattern:
                value: "^(yes|no)$"
                message: "Valid values: yes, no"
    readonly: False
    description: ""
    render:
      control: label_control
      display_name: "Users dict"
      constraints:
```
В данном примере все поля первого элемента массива users_dict являются нередактируемыми.

### additional
False - обязательное поле

True - дополнительное поле
#### Примечание
При отсутствии данного поля в метаданных параметра, по умолчанию оно будет считаться обязательным.

### id

Из-за генерации файла для визарда, id должны формироваться по следующему правилу.(Решение на данный момент)

1. id с номером 1 присваивается для 1 шага визарда(страница с выбором архитектуры)
2. Cледующие id присваиваются для каждой отдельной архитектуры. То есть, если в папке _framework/arch присутствует два файла arch1.yml и arch2.yml. То при заполнении файлов с метаданными id у параметров должны быть 2 и 3 соответственно
3. После выбора одной из архитектур инициализируются конфиг. файлы разных площадок и файл global.yml. Тогда в файлах с метаданными для global.yml параметры должны иметь id=4 
4. К примеру, есть две площадки mgmt с файлом common.yml и main с файлами common.yml и services_overrides.yml. Тогда ,учитывая, 2 пункт id с номером 5 уйдет под площадку mgmt, а id с номером 6 уйдет для шага визарда для заполнения конфига common.yml у mgmt. Поэтому в файле с метаданными для mgmt/common.yml у параметров id должен быть 6
5. Соотвественно у площадки main id будет 7, а в файлах с метаданными для конфигов common и services_overrides параметры будут иметь id 8 и 9 соответственно.

### render
Структура
```yaml
render:
  control:
  display_name: 
  constraints:
```
#### control
Обязательно для заполнения

| Наименование контрола | Типы данных(type или sub_type)              |
|-----------------------|---------------------------------------------|
| input_control         | string,string-single-quoted,string-double-quoted |
| textarea_control      | string,string-single-quoted,string-double-quoted |
| checkbox_control      | bool                                        |
| number_control        | int,double                                  |
| datetime_control      | datetime                                    |
| label_control         | array(sub_type=composite),dict              |
#### display_name
Строка с наимнованием параметра на пользовательском интерфейсе(обязательно для заполнения)
#### constraints
Ограничения для параметра

Структура:
```yaml
constraints:
  - constraint_name:
      value:
      message:
```
| constraint_name | value                 | тип данных          |
|-----------------|-----------------------|---------------------|
| pattern         | регулярное выражение  | string              |
| maxlength       | максимальная длина строки | int                 |
| minlength       | минимальная длина строки | int                 |
| min             | минимальное значение  | int,double,datetime |
| max             | максимальное значение | int,double,datetime |

## Описание метаданных в файлах навигации(wizard.meta,ui.meta)
wizard.meta - генерируется автоматически

ui.meta - заполняется самостоятельно
### Структура файла
```yaml
root:
  display_name: Root
  type: form
  id: 1
root/infras:
  description: Exist infrastructures
  display_name: Infrastructures
  type: form
  id: 2
root/infras/common:
  description: Configuration for infrastructure
  display_name: Common
  type: group
  id: 3
```
### Описание полей
| поле         | описание                                     | комментарий                                                                                                 |
|--------------|----------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| description  | краткое описание навигационного шага         |                                                                                                             |
| display_name | Наименование навигационного шага             |                                                                                                             |
| type         | Тип навигационного шага(form,group)          | Группа в пользовательском интерфейсе отображается на форме, <br/>к которой она принадлежит                  |
| id           | Уникальный идентификатор навигационного шага | Связь между метаданными параметра конфигурационного файла и <br/>формой(группой) определяется через этот id |