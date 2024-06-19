# **DTU 通信数据协议**

# 1 概述

本文档主要内容包括：
- 与云端通信的报文格式
- 所有命令模式的指令报文格式：设置参数、查询参数
- dtu_config.json配置文件字段的详细说明

# 2 数据格式

DTU与云端通信报文使用json格式

- 云端下行报文

命令模式：

`{“msg_id”: msg_id, “data”: “1234”[, “cmd_code”: 40, “topic_id”: 1]}`

透传模式：

`{“msg_id”: msg_id, “data”: “1234”}`

字段说明：

msg_id：报文id，一般为时间戳+3位随机数

data：报文消息字段

cmd_code：可选字段，填写对应功能码，并又DTU执行相应的操作，此字段仅在命令模式下生效

topic_id：可选字段，填写mqtt返回需要publish的topic_id，此字段仅在命令模式与使用MQTT/Aliyun/Txyun时生效

- modbus模式

`{“msg_id”: msg_id, “modbus”: {"groups": {"num": 0, "cmd": ["0x03", "0x00", "0x00", "0x00", "0x02"]}}}`

字段说明：

msg_id：报文id，一般为时间戳+3位随机数

data：报文消息字段

cmd_code：可选字段，填写对应功能码，并又DTU执行相应的操作，此字段仅在命令模式下生效

topic_id：可选字段，填写mqtt返回需要publish的topic_id，此字段仅在命令模式与使用MQTT/Aliyun/Txyun时生效

modbus：可选字段，此字段仅在modbus模式使用，此字段下有3个子字段：groups，task与command

&ensp;&ensp;&ensp;&ensp;groups：可选字段，在modbus模式下向指定的地址组发送消息

&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;num：配置文件中的地址组编号

&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;&ensp;cmd：向地址组发送的modbus命令

&ensp;&ensp;&ensp;&ensp;task：可选字段，在modbus模式下执行代码中预置的task任务

&ensp;&ensp;&ensp;&ensp;command：可选字段，在modbus下直接向UART口写入指定modbus命令

- 云端上行报文

命令模式：

`{"msg_id": msg_id, "data": "1234"[, "cmd_code": 40, "status": 1, "password": "123"]}`

透传模式：

`{“msg_id”: msg_id, “data”: “1234”}`

字段说明：

msg_id：报文id，一般为时间戳+3位随机数，回复报文会使用相同的msg_id

data：报文消息字段

cmd_code：可选字段，填写对应功能码，并又DTU执行相应的操作，此字段仅在命令模式下生效

status：可选字段，仅在命令模式下生效，用于反馈命令是否执行成功

# 3 指令说明

**协议功能码说明：**

**1 ．查询DTU ，复位DTU，设置参数，数据透传的功能码和返回数据的功能码一致**

**2.返回数据的状态码可查询对应的状态码表**

## 3.1 功能码表

| 功能码 | 功能                   |
| ------ | ---------------------- |
| 0-49   | 查询指令               |
| 0      | 查询IMEI               |
| 1      | 查询本机号码           |
| 2      | 查询项目版本号         |
| 3      | 查询信号强度           |
| 4      | 查询当前配置参数       |
| 5      | 诊断查询               |
| 6      | 查询ICCID              |
| 7      | 查询ADC电压            |
| 8      | 查询GPIO信息           |
| 10     | 查询温湿度             |
| 11     | 查询网络连接信息       |
| 12     | 查询网络状态           |
| 13     | 查询基站定位信息       |
| 50~143 | 设置指令               |
| 50     | 协议短信透传           |
| 51     | 配置密码               |
| 52     | 添加设备识别码IMEI     |
| 53     | 登录服务器发送注册信息 |
| 54     | 参数版本号             |
| 55     | 是否启用自动更新       |
| 56     | 日志输出               |
| 57     | 服务器获取配置参数     |
| 58     | 串口参数               |
| 59     | 通道配置参数           |
| 60     | Apn设置                |
| 61     | GPIO设置               |
| 62     | OTA                    |
| 63     | 参数设置               |
| 255    | 复位指令               |

# 4 查询指令

### 4.1.1 查询IMEI

**说明：**

DTU的IMEI号

功能码: 0

返回的数据内容：

`{"code": 0 , "data": "123456789012345" , "success":1}`

字段说明:

| **字段** | **类型** | **含义**                                                     |
| -------- | -------- | ------------------------------------------------------------ |
| code     | str      | 状态码（如果查询IMEI失败，可查询状态码表来定位具体错误信息） |
| data     | str      | 返回IMEI                                                     |
| success  | int      | 0 失败 1成功                                                 |

### 4.1.2 查询本机号码

**说明：**

查询SIM卡的号码

功能码: 1

返回的数据内容：

`{"code": 1 , "data": "17201593988" , "success":1}`

| **字段** | **类型** | **含义**        |
| -------- | -------- | --------------- |
| code     | Str      | 状态码          |
| data     | str      | SIM卡的手机号码 |
| success  | int      | 0 失败 1成功    |

### 4.1.3 查询项目版本号

**说明：**

查询当前的项目版本号（当开启fota升级，版本号小于服务器端的项目版本号会进行fota升级）

项目版本号格式为: 2.0.0

功能码: 2

返回的数据内容：

`{"code": 2 , "data": "2.0.0" , "success":1}`

| **字段** | **类型** | **含义**     |
| -------- | -------- | ------------ |
| code     | str      | 状态码       |
| data     | str      | 项目版本号   |
| success  | int      | 0 失败 1成功 |

### 4.1.4 查询信号强度

**说明：**

网络信号强度值范围0~31，值越大表示信号强度越好。

功能码: 3

返回的数据内容：

`{"code": 3 , "data": " CSQ17 " , "success":1}`

| **字段** | **类型** | **含义**     |
| -------- | -------- | ------------ |
| code     | str      | 状态码       |
| data     | str      | CSQ1~CSQ31   |
| success  | int      | 0 失败 1成功 |

### 4.1.5 查询当前配置参数

功能码: 4

数据内容：
```
{"password": "012345",
 "cmd_code": 4,
}
```
返回的数据内容：

`{"code": 4 , "data": " req config " , "success":1}`

| **字段** | **字符串** | **含义**     |
| -------- | ---------- | ------------ |
| code     | Str        | 状态码       |
| data     | str        | req config   |
| success  | int        | 0 失败 1成功 |

### 4.1.6 诊断查询

说明: 查询当前DTU运行的错误上报信息

功能码: 5

返回的数据内容：
```
{"code":5,

"data":[{"func_code": "5" , "error_code": " 6001"}],

"success":1}
```

| **字段**   | **类型** | **含义**     |
| ---------- | -------- | ------------ |
| code       | str      | 状态码       |
| func_code  | str      | 功能码       |
| error_code | str      | 错误码       |
| success    | int      | 0 失败 1成功 |

### 4.1.7 iccid查询

说明: 查询iccid

功能码: 6

返回的数据内容：
```
{"code":6,

"data": "12456465486561516515153",

"status":1}
```

| **字段** | **类型** | **含义**     |
| -------- | -------- | ------------ |
| code     | int      | 状态码       |
| data     | str      | 功能码       |
| status   | str      | 0 失败 1成功 |

### 4.1.8 adc查询

说明: 查询adc

功能码: 7

返回的数据内容：
```
{"code":7,

"data": "3.7",

"status":1}`
```
| **字段** | **类型** | **含义**     |
| -------- | -------- | ------------ |
| code     | int      | 状态码       |
| data     | str      | adc电压      |
| status   | str      | 0 失败 1成功 |

### 4.1.9 gpio查询

说明: 查询gpio

功能码: 8

返回的数据内容：
```
{"code":8,

"data": "gpio_msg",

"status":1}
```

| **字段** | **类型** | **含义**       |
| -------- | -------- | -------------- |
| code     | int      | 状态码         |
| data     | str      | gpio获取的信息 |
| status   | str      | 0 失败 1成功   |

### 4.1.10 电池电压查询

说明: 查询gpio

功能码: 9

返回的数据内容：
```
{"code":9,

"data": "3590",

"status":1}
```

| **字段** | **类型** | **含义**       |
| -------- | -------- | -------------- |
| code     | int      | 状态码         |
| data     | str      | gpio获取的信息 |
| status   | str      | 0 失败 1成功   |

### 4.1.10 查询温湿度

说明: 查询温湿度

功能码: 10

返回的数据内容：
```
{"code":10,
"data": {"temperature": 26.0, "humidity": 60.0},
"status":1}
```

| **字段** | **类型** | **含义**                                                   |
| -------- | -------- | ---------------------------------------------------------- |
| code     | int      | 状态码                                                     |
| data     | dict     | 温湿度信息{"temperature": temp, &#39;humidity&#39;: humid} |
| status   | str      | 0 失败 1成功                                               |

### 4.1.11 查询网络连接信息

说明: 查询网络连接信息,每种连接类型返回对应连接状态

功能码: 11

返回的数据内容：
```
{"code":11,
"data":{"1": 1},
"status":1}
```

| **字段** | **类型** | **含义**     |
| -------- | -------- | ------------ |
| code     | int      | 状态码       |
| data     | dict     | 各通道网络连接状态，key：通道号，value：网络连接状态 |
| status   | str      | 0 失败 1成功 |

网络连接状态说明

| **连接类型** | **含义**                                             |
| ------------ | ---------------------------------------------------- |
| udp           | 无意义（默认返回1）                                                |
| mqtt/aliyun/txyun/quecthing/tcp/http | 0：未连接成功 1：连接成功                   |

### 4.1.12 查询网络状态

说明: 查询网络连接状态,返回基站信息

功能码: 12

返回的数据内容：
```
{"code":12,

"data": {"voice_state": 1, "data_state": 1},

"status":1}
```

| **字段** | **类型** | **含义**                                          |
| -------- | -------- | ------------------------------------------------- |
| code     | int      | 状态码                                            |
| data     | turple   | voice_state:语音连接状态, data_state:数据连接状态 |
| status   | str      | 0 失败 1成功                                      |

状态说明

| **值** | **状态说明**                                                                                 |
| ------ | -------------------------------------------------------------------------------------------- |
| 0      | not registered, MT is not currently searching an operator to register to                     |
| 1      | registered, home network                                                                     |
| 2      | not registered, but MT is currently trying to attach or searching an operator to register to |
| 3      | registration denied                                                                          |
| 4      | unknown                                                                                      |
| 5      | registered, roaming                                                                          |
| 6      | egistered for “SMS only”, home network (not applicable)                                      |
| 7      | registered for “SMS only”, roaming (not applicable)                                          |
| 8      | attached for emergency bearer services only                                                  |
| 9      | registered for “CSFB not preferred”, home network (not applicable)                           |
| 10     | registered for “CSFB not preferred”, roaming (not applicable)                                |
| 11     | emergency bearer services only                                                               |

### 4.1.13 查询基站定位信息

说明: 查询基站定位信息

功能码: 13

返回的数据内容：
```
{"code":13,

"data": {"longitude": 31.82175827026367, "latitude": 117.1155395507812},

"status":1}
```

| **字段** | **类型** | **含义**     |
| -------- | -------- | ------------ |
| code     | int      | 状态码       |
| data     | dict     | 基站定位信息  |
| status   | str      | 0 失败 1成功 |


# 5 复位指令

功能码: 255

数据内容：
```
{"password":"",

"cmd_code": 255,

"data":{}

}
```

返回的数据内容：

无

| **字段** | **类型** | **含义**     |
| -------- | -------- | ------------ |
| code     | Str      | 状态码       |
| data     | str      | reset dtu    |
| success  | int      | 0 失败 1成功 |

# 6 设置指令

## 6.1 基础设置

### 6.1.1 协议短信(SMS)透传 message

功能码: 50

数据内容：

- 号码：32个字节，标识目的手机号码,如果没有32字节，必须补0x00
- 内容：最大1024字节，为短信数据内容
```
{

"password":"",
"cmd_code": 50,
"data":{

message: {"number":"12123123", -- 目标号码

"sms_msg:" " -- 发送短信

}
}
}
```

返回的数据内容：

`{"code": 50 , "data": " " , "success":1}`

| **字段** | **类型** | **含义**     |
| -------- | -------- | ------------ |
| code     | str      | 状态码       |
| data     | str      | 接收的短信   |
| success  | int      | 0 失败 1成功 |

### 6.1.2 配置密码 password

**说明：**

查询IMEI,查询本机号码，查询参数版本号，查询信号强度不需要密码

查询当前配置参数和修改透传绑定的通道需要密码

是否开启自动更新需要密码

功能码: 51

数据内容：
```
{
"password":" ",
"cmd_code": 51,
"data":{"new_password": "012345"}
}
```
说明：初始密码为固件IMEI的后六位

如 IMEI : 123456789012345 初始密码为 012345

| **字段** | **含义**                |
| -------- | ----------------------- |
| password | 当前密码                 |
| data     | password : 修改后的密码  |

返回的数据内容：

`{"code": 51 , "data": " " , "success":1}`

| **字段** | **含义**     |
| -------- | ------------ |
| code     | 状态码       |
| data     |
|          |
| success  | 0 失败 1成功 |

### 6.1.3 登录服务器发送注册信息 reg

**说明：**

首次登陆服务器发送注册信息

功能码: 53

数据内容：
```
{
"password":"",
"cmd_code": 53,
"data":{"reg": 1}
}
```

| **Reg** | **值**                                                                                                                                                            |
| ------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 0       | 不发送{ "reg": 0}                                                                                                                                                 |
| 1       | { "reg": 1}则首次登录服务器发送下面的json数据： {"csq":rssi,"imei":imei,"iccid":iccid,"ver":version}csq 信号强度imei 固件的imeiiccid SIM卡的iccidver 固件的版本号 |
| 自定义  | { "reg": "自定义的注册信息"}                                                                                                                                      |

返回的数据内容：

`{"code": 53 , "data": " " , "success":1}`

| **字段** | **类型** | **含义**     |
| -------- | -------- | ------------ |
| code     | str      | 状态码       |
| data     | str      | send reg     |
| success  | int      | 0 失败 1成功 |

### 6.1.4 设置参数版本号

**说明：**

设置参数版本号

功能码: 54

数据内容：
```
{
"password":"",
"cmd_code": 54,
"data": {"version": 1}
}
```
返回的数据内容：

`{"code": 54 , "data": 2, "success":1}`

| **字段** | **类型** | **含义**     |
| -------- | -------- | ------------ |
| code     | str      | 状态码       |
| data     | dict      | 1~n参数版本号         |
| success  | int      | 0 失败 1成功 |

### 6.1.5 是否启用自动更新 fota

**说明：**

Fota升级开关

功能码: 55

数据内容：
```
{
"password":"",
"cmd_code": 55,
"data":{
"fota": 1 -- 0关闭/ 1 开启（int类型）
}
}
```
返回的数据内容：

`{"code": 55 , "data": " fota" , "success":1}`

| **字段** | **类型** | **含义**     |
| -------- | -------- | ------------ |
| code     | str      | 状态码       |
| data     | str      | fota         |
| success  | int      | 0 失败 1成功 |

### 6.1.6 日志输出 nolog

**说明：**

串口打印日志记录,目前不支持。日志输出连接Debug口

功能码: 56

数据内容：
```
{
"password":"",
"cmd_code": 56,
"data":{
{"nolog": 1} 是否开启日志 0关闭/1打开（int类型）
}
}
```
返回的数据内容：

`{"code": "20000" , "data": "log " , "success":1}`

| **字段** | **类型** | **含义**     |
| -------- | -------- | ------------ |
| code     | Str      | 状态码       |
| data     | str      | log          |
| success  | int      | 0 失败 1成功 |

### 6.1.7 服务器获取配置参数

功能码: 57

数据内容：
```
{
"password":"",
"cmd_code": 57,
"data":{
{" service_acquire"：0}
}
}
```
注:本地配置默认开启向服务器获取参数配置

| **字段**        | **类型** | **含义**                          |
| --------------- | -------- | --------------------------------- |
| service_acquire | Int      | 是否开启服务器获取参数0关闭/1打开 |

返回的数据内容：

`{"code": "20000" , "data": "service acquire " , "success":1}`

| **字段** | **类型** | **含义**        |
| -------- | -------- | --------------- |
| code     | Str      | 状态码          |
| data     | str      | service acquire |
| success  | int      | 0 失败 1成功    |

### 6.1.8 串口参数 uconf

功能码: 58

**在透传模式下无法设置串口参数**

数据内容：
```
{"password": ""
"cmd_code": 58,
"data":{
"uconf": {
"0": {
"baudrate": "115200",
"databits": "8",
"parity": "0",
"stopbits": "1",
"flowctl": "0"
}
}}
```
返回的数据内容：

`{"code": "20000" , "data": " " , "success":1}`

| **字段** | **类型** | **含义**     |
| -------- | -------- | ------------ |
| code     | Str      | 状态码       |
| data     | str      | uconf        |
| success  | int      | 0 失败 1成功 |

### 6.1.9 通道配置参数 conf

功能码: 59

**在透传模式下无法设置通道配置参数**

数据内容：
```
{"password":"",
 "cmd_code": 59,
 "data":{
     "conf":{
         "1": {
            "protocol": "aliyun",
            "type": "mos",
            "keepAlive": "",
            "clientID": "0",
            "Devicename": "dtu_device1",
            "ProductKey": "gzsi5zT5fH3",
            "DeviceSecret": "173f006cab770615346978583ac430c0",
            "ProductSecret": "D07Ujh1RvKAs6KEY",
            "cleanSession": true,
            "qos": "1",
            "subscribe": {"0": "/gzsi5zT5fH3/dtu_device1/user/get"},
            "publish": {"0": "/gzsi5zT5fH3/dtu_device1/user/update"},
            "serialID": 2}
}}}
```
**对应通道的配置参数详见6.1.9.1的通道配置详解 ：**

返回的数据内容：

`{"code": "20000" , "data": " " , "success":1}`

| **字段** | **类型** | **含义**     |
| -------- | -------- | ------------ |
| code     | str      | 状态码       |
| data     | str      | conf         |
| success  | int      | 0 失败 1成功 |

#### 6.1.10.1 通道配置详解

##### 6.1.10.1.1 HTTP参数
```
{
"protocol": "http",
"request": {"1":{"method":"get", "url":"http://220.180.239.212:18011/test"}},
"post_data": "",
"serialID": 2
}
```
| **字段** | **类型** | **含义**                |
| -------- | -------- | ----------------------- |
| http     | str      | 通信方式http标识        |
| request  | dict     | HTTP请求的id,对应实际和http服务器通信的mothod和url|
| post_data | str      | post请求携带的数据，get请求不填写|
| serialD  | int      | HTTP绑定的串口号（1~2） |

##### 6.1.10.1.2 SOCKET tcp参数
```
{
"protocol": "tcp",
"ip_type":"IPv4",
"server": "220.180.239.212",
"port": "18011",
"keep_alive": 5,
"serialID": 2
}
```
| **字段**  | **类型** | **含义**                                          |
| --------- | -------- | ------------------------------------------------- |
| tcp       | str      | Socket的tcp协议标识                               |
| ip_type   | str      | IPv4或者IPv6 |
| server    | str      | socket的地址或域名                                |
| port      | int      | socket服务器的端口号                              |
| keep_alive | int     | 心跳间隔时间，单位分钟                              |
| serialD   | int      | tcp/udp绑定的串口号(1~2)                          |

##### 6.1.10.1.3 SOCKET udp 参数
```
{
"protocol": "udp",
"ip_type":"IPv4",
"server": "220.180.239.212",
"port": "18011",
"serialID": 2
}
```
| **字段**  | **类型** | **含义**                                          |
| --------- | -------- | ------------------------------------------------- |
| protocol  | str      | Socket的udp协议标识                              |
| ip_type   | str      | IPv4或者IPv6 |
| server    | str      | socket的地址或域名                                |
| port      | int      | socket服务器的端口号                              |
| serialD   | int      | tcp/udp绑定的串口号(1~2)                          |

##### 6.1.10.1.4 MQTT参数
```
{
"protocol": "mqtt",
"clientID": "test_mqtt",
"keepAlive": 0,
"url": "broker-cn.emqx.io",
"port": "1883",
"cleanSession": true,
"subscribe": {"0": "/python/mqtt"},
"publish": {"0": "/python/mqtt"},
"qos": "0",
"retain": "1",
"serialID": "1"
}
```
| **字段**     | **类型** | **含义**                                       |
| ------------ | -------- | ---------------------------------------------- |
| mqtt         | str      | 表示MQTT协议                                   |
| clentID      | str      | 自定义客户端ID，使用IMEI做客户端ID此处留空     |
| keepAlive    | int      | 客户端的keepalive超时值。 默认为60秒           |
| url          | str      | MQTT的地址或域名                               |
| port         | int      | socket服务器的端口号                           |
| cleanSession | int      | MQTT是否保存会话标志位,0持久会话,1离线自动销毁 |
| subscribe    | str      | 订阅主题                                       |
| publish      | str      | 发布主题                                       |
| qos          | int      | MQTT的QOS级别,默认0                            |
| retain       | int      | MQTT的publish参数retain，默认0                 |
| serialD      | int      | MQTT通道捆绑的串口ID (1~3)                     |

##### 6.1.10.1.5 阿里云参数
```
{
"protocol": "aliyun",
"type": "mos",
"keepAlive": "",
"clientID": "0",
"Devicename": "dtu_device1",
"ProductKey": "gzsi5zT5fH3",
"DeviceSecret": "173f006cab770615346978583ac430c0",
"ProductSecret": "D07Ujh1RvKAs6KEY",
"cleanSession": true,
"qos": "1",
"subscribe": {"0": "/gzsi5zT5fH3/dtu_device1/user/get"},
"publish": {"0": "/gzsi5zT5fH3/dtu_device1/user/update"},
"serialID": 2
}
```
| **字段**      | **类型** | **含义**                                                                                                                                      |
| ------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| aliyun        | Str      | 阿里云IOT的标识                                                                                                                               |
| type          | str      | 一型一密tas/一机一密mos                                                                                                                       |
| keepAlive     | int      | 通信之间允许的最长时间段（以秒为单位）,默认为300，范围（60-1200）使用默认值就填""或者" "                                                      |
| clientID      | str      | clientID ,自定义字符（不超过64）                                                                                                              |
| Devicename    | str      | 设备名称                                                                                                                                      |
| ProductKey    | str      | 产品密钥                                                                                                                                      |
| DeviceSecret  | str      | 设备密钥（使用一型一密认证此参数传入"")                                                                                                       |
| ProductSecret | str      | 产品密钥（使用一机一密认证时此参数传入"")                                                                                                     |
| cleanSession   | bool     | 配置与云平台通信的数据是否采用session加密（默认值为False），True：加密，False：加密                                    |
| qos           | int      | MQTT消息服务质量（默认0，可选择0或1）0：发送者只发送一次消息，不进行重试 1：发送者最少发送一次消息，确保消息到达Broker                        |
| subscribe      | str      | 订阅主题                                                                                                                                      |
| publish      | str      | 发布主题                                                                                                                                      |
| serialD       | int      | MQTT通道捆绑的串口ID (1~3)                                                                                                                    |

##### 6.1.10.1.6 腾讯云参数
```
{
"protocol": "txyun",
"type": "mos",
"keepAlive": "",
"clientID": "0",
"Devicename": "dtu_device1",
"ProductKey": "I81T7DUSFF",
"DeviceSecret": "wF+b5NwEHI53crHmOqdyQA==",
"ProductSecret": "",
"cleanSession": "0",
"qos": "1",
"subscribe": {"0": "I81T7DUSFF/dtu_device1/control"},
"publish": {"0": "I81T7DUSFF/dtu_device1/event"},
"serialID": 0
}
```
| **字段**      | **类型** | **含义**                                                                                                                                      |
| ------------- | -------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| txyun         | str      | 腾讯云IOT的标识                                                                                                                               |
| type          | str      | 一型一密tas/一机一密mos                                                                                                                       |
| keepAlive     | int      | 通信之间允许的最长时间段（以秒为单位）,默认为300，范围（60-1200）使用默认值就填""或者" "。                                                    |
| clientID      | str      | clientID ,自定义字符（不超过64）                                                                                                              |
| Devicename    | str      | 设备名称                                                                                                                                      |
| ProductKey    | str      | 产品密钥                                                                                                                                      |
| DeviceSecret  | str      | 设备密钥（使用一型一密认证此参数传入"")                                                                                                       |
| ProductSecret | str      | 产品密钥（使用一机一密认证时此参数传入"")                                                                                                     |
| cleanSession   | bool     | 配置与云平台通信的数据是否采用session加密（默认值为False），True：加密，False：加密                                    |
| QOS           | int      | MQTT消息服务质量（默认0，可选择0或1）0：发送者只发送一次消息，不进行重试 1：发送者最少发送一次消息，确保消息到达Broker                        |
| subscribe      | str      | 订阅主题                                                                                                                                      |
| publish      | str      | 发布主题                                                                                                                                      |
| serialD       | int      | MQTT通道捆绑的串口ID (1~3)                                                                                                                    |


##### 6.1.10.1.7 移远云参数
```
{
"protocol": "quecthing",
"keepAlive": "",
"ProductKey": "p113LS",
"ProductSecret": "ZjY3bGFtTUpsL1RN",
"Devicename": "dtudevice1",
"DeviceSecret":"",
"qos": "1",
"SessionFlag": false,
"sendMode": "pass",
"serialID": "2"
}
```
| **字段**      | **类型** | **含义**                                                                                                               |
| ------------- | -------- | ---------------------------------------------------------------------------------------------------------------------- |
| quecthing     | str      | 移远云IOT的标识                                                                                                        |
| keepAlive     | int      | 通信之间允许的最长时间段（以秒为单位）,默认为120，范围（60-1200）使用默认值就填""或者" "。                             |
| ProductKey    | str      | 产品id                                                                                                                 |
| ProductSecret | str      | 产品密钥                                                                                                               |
| Devicename    | str      | 设备名称                                                                                                                |
| DeviceSecret  | str      | 设备密钥 
| qos           | int      | MQTT消息服务质量（默认0，可选择0或1）0：发送者只发送一次消息，不进行重试 1：发送者最少发送一次消息，确保消息到达Broker |
| SessionFlag   | bool     | 配置与云平台通信的数据是否采用session加密（默认值为False），True：加密，False：加密                                    |
| sendMode      | str      | 移远云数据收发模式，phy：物模型，pass：透传                                                                            |
| serialD       | int      | MQTT通道捆绑的串口ID (1~3)                                                                                             |


移远云开发说明请点击以下连接获取文档：

[Quectel_移远通信物联网设备管理平台设备接入_应用指导_(Python)_2.9.0.pdf](https://quec-pro-oss.oss-cn-shanghai.aliyuncs.com/documentCenter/Quectel_%E7%A7%BB%E8%BF%9C%E9%80%9A%E4%BF%A1%E7%89%A9%E8%81%94%E7%BD%91%E8%AE%BE%E5%A4%87%E7%AE%A1%E7%90%86%E5%B9%B3%E5%8F%B0%E8%AE%BE%E5%A4%87%E6%8E%A5%E5%85%A5_%E5%BA%94%E7%94%A8%E6%8C%87%E5%AF%BC_(Python)_2.9.0.pdf)

##### 6.1.10.1.8 华为云参数
```
{
"protocol": "hwyun",
"url": "a15fbbd7ce.iot-mqtts.cn-north-4.myhuaweicloud.com",
"port": "1883",
"Devicename": "625132b420cfa22b94c54613_dtu_device1_id",
"DeviceSecret": "a306255686a71e56ad53965fc2771bf8",
"keep_alive": 10,
"cleanSession": true,
"subscribe": {"0": "$oc/devices/625132b420cfa22b94c54613_dtu_device1_id/sys/messages/down"},
"publish": {"0": "$oc/devices/625132b420cfa22b94c54613_dtu_device1_id/sys/messages/up"},
"qos": 0,
"serialID": 2
}
```
| **字段**      | **类型** | **含义**                                                                                                               |
| ------------- | -------- | ---------------------------------------------------------------------------------------------------------------------- |
| hwyun         | str      | 华为云IOT的标识                                                                                                        |
| url           | str      | MQTT的地址或域名                                                                                                       |
| port          | int      | socket服务器的端口号                                                                                                    |
| Devicename    | str      | 设备名称                                                                                                                |
| DeviceSecret  | str      | 设备密钥 
| keepAlive     | int      | 通信之间允许的最长时间段（以秒为单位）,默认为120，范围（60-1200）使用默认值就填""或者" "。                             |
| cleanSession   | bool     | 配置与云平台通信的数据是否采用session加密（默认值为False），True：加密，False：加密                                    |
| subscribe    | str      | 订阅主题                                       |
| publish      | str      | 发布主题                                       |
| qos           | int      | MQTT消息服务质量（默认0，可选择0或1）0：发送者只发送一次消息，不进行重试 1：发送者最少发送一次消息，确保消息到达Broker |
| serialD       | int      | MQTT通道捆绑的串口ID (1~3)                                                                                             |


华为云开发说明请点击以下连接获取文档：

(https://python.quectel.com/doc/doc/Advanced_development/zh/QuecPythonCloud/HuaweiCloud.html)


# 7 设置APN

说明：这个指令只适合配置和使用不是同一张卡的场景

**在透传模式下无法设置串口参数**

功能码: 60

数据内容：
```
{
"password":" ",
"data":{"apn": ["", "", ""]}
}
```
apn对应列表说明:

列表第一个参数: apn 的名称

列表第二个参数: apn 的用户名

列表第三个参数: apn 的密码

返回的数据内容：

`{"code": 60 , "status":1}`

| **字段** | **类型** | **含义**     |
| -------- | -------- | ------------ |
| code     | Str      | 状态码       |
| data     | str      | set apn      |
| success  | int      | 0 失败 1成功 |

# 8 GPIO pins

功能码: 61

**在透传模式下无法设置串口参数**

pins的长度必须为3

数据内容：
```
{"password": " ",
"data":{"pins":[
"1", -- 网路指示灯的GPIO (pio1~pio128)
"2", -- 与服务器连上后通知GPIO (pio1~pio128)
"3" -- 重置DTU参数的GPIO (pio1~pio128)
]}}
```
返回的数据内容：

`{"code": 61 , "status":1}`

| **字段** | **类型** | **含义**      |
| -------- | -------- | ------------- |
| code     | Str      | 状态码        |
| data     | str      | set gpio pins |
| success  | int      | 0 失败 1成功  |

# 9 OTA

功能码: 62

数据内容：
```
{"password": " ",
"data":{"ota":1}
}
```
返回的数据内容：

`{"code": 62 , "status":1}`

| **字段** | **类型** | **含义**     |
| -------- | -------- | ------------ |
| code     | Str      | 状态码       |
| data     | str      | OTA状态      |
| status   | int      | 0 失败 1成功 |


# 10 参数设置

功能码: 63

数据内容：
```
{"password": " ",
"data":{"dtu_config":{完整配置文件内容}
}
```

完整配置文件参照《DTU上手说明》

返回的数据内容：

`{"code": 63 , "status":1}`

| **字段** | **类型** | **含义**     |
| -------- | -------- | ------------ |
| code     | Str      | 状态码       |
| status   | int      | 0 失败 1成功 |
