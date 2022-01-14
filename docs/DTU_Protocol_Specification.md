## 修订历史

| Version | **Date**   | **Author** | **Change expression** |
| :------ | ---------- | ---------- | --------------------- |
| 1.0     | 2021-11-25 | 陈驰      | 初始版本              |

## 概述

本文档主要内容包括：
- 与云端通信的报文格式
- 所有命令模式的指令报文格式：设置参数、查询参数
- dtu_config.json配置文件字段的详细说明

## 数据格式

DTU与云端通信报文使用json格式

- 云端下行报文

命令模式与modbus模式：

`{“msg_id”: msg_id, “data”: “1234”[, “cmd_code”: 0X40, “topic_id”: 1]}`

透传模式：

`{“msg_id”: msg_id, “data”: “1234”}`

字段说明：

msg_id：报文id，一般为时间戳+3位随机数

data：报文消息字段

cmd_code：可选字段，填写对应功能码，并又DTU执行相应的操作，此字段仅在命令模式下生效

topic_id：可选字段，填写mqtt返回需要publish的topic_id，此字段仅在命令模式与使用MQTT/Aliyun/Txyun时生效

- 云端上行报文

命令模式与modbus模式：

`{“msg_id”: msg_id, “data”: “1234”[, “cmd_code”: 0X40, “status”: 1]}`

透传模式：

`{“msg_id”: msg_id, “data”: “1234”}`

字段说明：

msg_id：报文id，一般为时间戳+3位随机数，回复报文会使用相同的msg_id

data：报文消息字段

cmd_code：可选字段，填写对应功能码，并又DTU执行相应的操作，此字段仅在命令模式下生效

status：可选字段，仅在命令模式下生效，用于反馈命令是否执行成功

## 指令说明

**协议功能码说明：**

**1 ．查询DTU ，复位DTU，设置参数，数据透传的功能码和返回数据的功能码一致**

**2.返回数据的状态码可查询对应的状态码表**

### 功能码表

| 功能码 | 功能 |
| --- | --- |
| 0x00-0x3f | 查询指令 |
| 0x00 | 查询IMEI |
| 0x01 | 查询本机号码 |
| 0x02 | 查询固件版本号 |
| 0x03 | 查询信号强度 |
| 0x04 | 查询当前配置参数 |
| 0x05 | 诊断查询 |
| 0X06 | 查询ICCID |
| 0X07 | 查询ADC电压 |
| 0X08 | 查询GPIO信息 |
| 0X10 | 查询温湿度 |
| 0X11 | 查询网络连接信息 |
| 0X12 | 查询网络状态 |
| 0X13 | 查询基站定位信息 |
| 0x50~0x8f | 设置指令 |
| 0x50 | 协议短信透传 |
| 0x51 | 配置密码 |
| 0x52 | 添加设备识别码IMEI |
| 0x53 | 登录服务器发送注册信息 |
| 0x54 | 固件版本号 |
| 0x55 | 是否启用自动更新 |
| 0x56 | 日志输出 |
| 0x57 | 服务器获取配置参数 |
| 0x58 | 串口参数 |
| 0x59 | 通道配置参数 |
| 0x60 | Apn设置 |
| 0x61 | GPIO设置 |
| 0x62 | GPS |
| 0x63 | 数据流 |
| 0x64 | 预警 |
| 0x65 | 任务 |
| 0xfd | 协议终止指令 |
| 0xfe | DTU启动中，无法接收指令 |
| 0xff | 复位指令 |

## 查询指令

### 查询IMEI

**说明：**

DTU的IMEI号

功能码: 0x00

返回的数据内容：

`{"code": 0x00 , "data": "123456789012345" , "success":1}`

字段说明:

| **字段** | **类型** | **含义** |
| --- | --- | --- |
| code | str | 状态码（如果查询IMEI失败，可查询状态码表来定位具体错误信息） |
| data | str | 返回IMEI |
| success | int | 0 失败 1成功 |

### 查询本机号码

**说明：**

查询SIM卡的号码

功能码: 0x01

返回的数据内容：

`{"code": 0x01 , "data": "17201593988" , "success":1}`

| **字段** | **类型** | **含义** |
| --- | --- | --- |
| code | Str | 状态码 |
| data | str | SIM卡的手机号码 |
| success | int | 0 失败 1成功 |

### 查询固件版本号

**说明：**

查询当前的固件版本号（当开启fota升级，版本号小于服务器端的固件版本号会进行fota升级）

固件版本号格式为: v 1

功能码: 0x02

返回的数据内容：

`{"code": 0x02 , "data": "v 1" , "success":1}`

| **字段** | **类型** | **含义** |
| --- | --- | --- |
| code | str | 状态码 |
| data | str | 固件版本号 |
| success | int | 0 失败 1成功 |

### 查询信号强度

**说明：**

网络信号强度值范围0~31，值越大表示信号强度越好。

功能码: 0x03

返回的数据内容：

`{"code": 0x03 , "data": " CSQ17 " , "success":1}`

| **字段** | **字符串** | **含义** |
| --- | --- | --- |
| code | str | 状态码 |
| data | str | CSQ1~CSQ31 |
| success | int | 0 失败 1成功 |

### 查询当前配置参数

功能码: 0x04

数据内容：
```
{ "password": "012345",

"data":{}

}
```
返回的数据内容：

`{"code": 0x04 , "data": " req config " , "success":1}`

| **字段** | **字符串** | **含义** |
| --- | --- | --- |
| code | Str | 状态码 |
| data | str | req config |
| success | int | 0 失败 1成功 |

### 诊断查询

说明: 查询当前DTU运行的错误上报信息

功能码: 0x05

返回的数据内容：
```
{"code":0x05,

"data":[{"func_code": "0x01" , "error_code": " 6001"}],

"success":1}
```

| **字段** | **类型** | **含义** |
| --- | --- | --- |
| code | str | 状态码 |
| func_code | str | 功能码 |
| error_code | str | 错误码 |
| success | int | 0 失败 1成功 |

### iccid查询

说明: 查询iccid

功能码: 0x06

返回的数据内容：
```
{"code":0x06,

"data": "12456465486561516515153",

"status":1}
```

| **字段** | **类型** | **含义** |
| --- | --- | --- |
| code | int | 状态码 |
| data | str | 功能码 |
| status | str | 0 失败 1成功 |

### adc查询

说明: 查询adc

功能码: 0x07

返回的数据内容：
```
{"code":0x07,

"data": "3.7",

"status":1}`
```
| **字段** | **类型** | **含义** |
| --- | --- | --- |
| code | int | 状态码 |
| data | str | adc电压 |
| status | str | 0 失败 1成功 |

### gpio查询

说明: 查询gpio

功能码: 0x08

返回的数据内容：
```
{"code":0x08,

"data": "gpio_msg",

"status":1}
```

| **字段** | **类型** | **含义** |
| --- | --- | --- |
| code | int | 状态码 |
| data | str | gpio获取的信息 |
| status | str | 0 失败 1成功 |

### 查询温湿度

说明: 查询温湿度

功能码: 0x010

返回的数据内容：
```
{"code":0x10,
"data": {"temperature": 26.0, "humidity": 60.0},
"status":1}
```

| **字段** | **类型** | **含义** |
| --- | --- | --- |
| code | int | 状态码 |
| data | dict | 温湿度信息{"temperature": temp, &##39;humidity&##39;: humid} |
| status | str | 0 失败 1成功 |

### 查询网络连接信息

说明: 查询网络连接信息,每种连接类型返回对应连接状态

功能码: 0x11

返回的数据内容：
```
{"code":0x11,
"data": "200",
"status":1}
```

| **字段** | **类型** | **含义** |
| --- | --- | --- |
| code | int | 状态码 |
| data | str | 网络连接状态 |
| status | str | 0 失败 1成功 |

### 查询网络状态

说明: 查询网络连接状态,返回基站信息

功能码: 0x12

返回的数据内容：
```
{"code":0x12,

"data": ([], [], [(0, 14071232, 1120, 0, 123….),

"status":1}
```

| **字段** | **类型** | **含义** |
| --- | --- | --- |
| code | int | 状态码 |
| data | turple | 基站连接状态 |
| status | str | 0 失败 1成功 |

### 查询基站定位信息

说明: 查询基站定位信息

功能码: 0x13

返回的数据内容：
```
{"code":0x13,

"data": (117.1138, 31.82279, 550) ,

"status":1}
```

| **字段** | **类型** | **含义** |
| --- | --- | --- |
| code | int | 状态码 |
| data | str | 基站定位信息 |
| status | str | 0 失败 1成功 |

## 复位指令

功能码: 0xff

数据内容：
```
{ Password: "012345",

"data":{}

}
```

返回的数据内容：

`{"code": 0x06 , "data": " reset dtu " , "success":1}`

| **字段** | **类型** | **含义** |
| --- | --- | --- |
| code | Str | 状态码 |
| data | str | reset dtu |
| success | int | 0 失败 1成功 |

## 设置指令

### 基础设置

#### 协议短信(SMS)透传 message

功能码: 0x50

数据内容：

- 号码：32个字节，标识目的手机号码,如果没有32字节，必须补0x00
- 内容：最大1024字节，为短信数据内容
```
{

"password":"",

"data":{

message: {"number":"12123123", -- 目标号码

"data:" " -- 发送短信

}
}
}
```

返回的数据内容：

`{"code": 0x50 , "data": " " , "success":1}`

| **字段** | **类型** | **含义** |
| --- | --- | --- |
| code | str | 状态码 |
| data | str | 接收的短信 |
| success | int | 0 失败 1成功 |

#### 配置密码 password

**说明：**

查询IMEI,查询本机号码，查询固件版本号，查询信号强度不需要密码

查询当前配置参数和修改透传绑定的通道需要密码

是否开启自动更新需要密码

功能码: 0x51

数据内容：
```
{
"password":" ",
"data":{ "password": "012345"}
}
```
说明：初始密码为固件IMEI的后六位

如 IMEI : 123456789012345 初始密码为 012345

| **字段** | **含义** |
| --- | --- |
| password | 当前密码 |
| data | password : 修改后的密码 |

返回的数据内容：

`{"code": 0x51 , "data": " " , "success":1}`

| **字段** | **含义** |
| --- | --- |
| code | 状态码 |
| data |
 |
| success | 0 失败 1成功 |

#### 登录服务器发送注册信息 reg

**说明：**

首次登陆服务器发送注册信息

功能码: 0x53

数据内容：
```
{
"password":"",
"data":{"reg": 1}
}
```

| **Reg**| **值** |
| --- | --- |
| 0 | 不发送{ "reg": 0} |
| 1 | { "reg": 1}则首次登录服务器发送下面的json数据： {"csq":rssi,"imei":imei,"iccid":iccid,"ver":version}csq 信号强度imei 固件的imeiiccid SIM卡的iccidver 固件的版本号 |
| 自定义 | { "reg": "自定义的注册信息"} |

返回的数据内容：

`{"code": 0x53 , "data": " " , "success":1}`

| **字段** | **类型** | **含义** |
| --- | --- | --- |
| code | str | 状态码 |
| data | str | send reg |
| success | int | 0 失败 1成功 |

#### 固件版本号 version

**说明：**

修改固件版本号，用于fota升级（当开启fota升级，版本号小于服务器端的固件版本号就会进行fota升级）

功能码: 0x54

数据内容：
```
{
"password":"",
"data":{
" version ": "100" --- 版本号（使用数字字符串）
}
}
```

返回的数据内容：

`{"code": 0x54 , "data": " " , "success":1}`

| **字段** | **类型** | **含义** |
| --- | --- | --- |
| code | Str | 状态码 |
| data | str | 固件版本号 |
| success | int | 0 失败 1成功 |

#### 是否启用自动更新 fota

**说明：**

Fota升级开关

功能码: 0x55

数据内容：
```
{
"password":"",
"data":{
"fota": 1 -- 0关闭/ 1 开启（int类型）
}
}
```
返回的数据内容：

`{"code": 0x55 , "data": " fota" , "success":1}`

| **字段** | **类型** | **含义** |
| --- | --- | --- |
| code | str | 状态码 |
| data | str | fota |
| success | int | 0 失败 1成功 |

#### 日志输出 nolog

**说明：**

串口打印日志记录,目前不支持。日志输出连接Debug口

功能码: 0x56

数据内容：
```
{
"password":"",
"data":{
{"nolog": 1} 是否开启日志 0关闭/1打开（int类型）
}
}
```
返回的数据内容：

`{"code": "20000" , "data": "log " , "success":1}`

| **字段** | **类型** | **含义** |
| --- | --- | --- |
| code | Str | 状态码 |
| data | str | log |
| success | int | 0 失败 1成功 |

#### 服务器获取配置参数

功能码: 0x57

数据内容：
```
{
"password":"",
"data":{
{" service_acquire"：0}
}
}
```
注:本地配置默认开启向服务器获取参数配置

| **字段** | **类型** | **含义** |
| --- | --- | --- |
| service_acquire | Int | 是否开启服务器获取参数0关闭/1打开|

返回的数据内容：

`{"code": "20000" , "data": "service acquire " , "success":1}`

| **字段** | **类型** | **含义** |
| --- | --- | --- |
| code | Str | 状态码 |
| data | str | service acquire |
| success | int | 0 失败 1成功 |

#### 串口参数 uconf

功能码: 0x58

数据内容：
```
{"password": ""
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

| **字段** | **类型** | **含义** |
| --- | --- | --- |
| code | Str | 状态码 |
| data | str | uconf |
| success | int | 0 失败 1成功 |

#### 通道配置参数 conf

功能码: 0x59

数据内容：
```
{"password":"",
"data":{
"conf":"1": {
"protocol": "aliyun",
"type": "mos",
"keepAlive": "",
"clientID": "0",
"Devicename": "ec600n",
"ProductKey": "gbh26bFEA4M",
"DeviceSecret": "b7ff5acc0671d40adfd0eff57e7605f6",
"ProductSecret": "",
"cleanSession": true,
"qos": "1",
"subscribe": {"0": "/gbh26bFEA4M/ec600n/user/subtest"},
"publish": {"0": "/gbh26bFEA4M/ec600n/user/pubtest"},
"serialID": "0"}
}}
```
**对应通道的配置参数详见6.1.10.1的通道配置详解 ：**

返回的数据内容：

`{"code": "20000" , "data": " " , "success":1}`

| **字段** | **类型** | **含义** |
| --- | --- | --- |
| code | str | 状态码 |
| data | str | conf |
| success | int | 0 失败 1成功 |

##### 通道配置详解

###### HTTP参数
```
{
"protocol": "http",
"method": "get",
"url": "http://httpbin.org/get",
"reg_data": "",
"timeout": "",
"serialID": 1
}
```
| **字段** | **类型** | **含义** |
| --- | --- | --- |
| http | str | 通信方式http标识 |
| method | str | 提交请求的方法 |
| url | str | HTTP请求的地址和参数 |
| timeout | int | HTTP请求最长等待时间 |
| serialD | int | HTTP绑定的串口号（1~2） |

###### SOCKET tcp参数
```
{
"protocol": "tcp",
"ping": "",
"heartbeat": 30,
"url": "220.180.239.212",
"port": "8305",
"keepAlive": 300,
"serialID": 2
}
```
| **字段** | **类型** | **含义** |
| --- | --- | --- |
| tcp | str | Socket的tcp协议标识 |
| ping | str | 用户自定义的心跳包,只支持数字和字母,建议2-4个字节 |
| time | int | 0为关闭心跳包，建议60s-300s |
| url | str | socket的地址或域名 |
| port | int | socket服务器的端口号 |
| KeepAlive | int | 链接超时最大时间单位秒,默认300秒 |
| serialD | int | tcp/udp绑定的串口号(1~2) |

###### SOCKET udp 参数
```
{
"protocol": "tcp",
"ping": "",
"heartbeat": 30,
"url": "220.180.239.212",
"port": "8305",
"keepAlive": 300,
"serialID": 2
}
```
| **字段** | **类型** | **含义** |
| --- | --- | --- |
| udp | str | Socket的udp协议标识 |
| ping | str | 用户自定义的心跳包,只支持数字和字母,建议2-4个字节 |
| time | int | 0为关闭心跳包，建议60s-300s |
| url | str | socket的地址或域名 |
| port | int | socket服务器的端口号 |
| KeepAlive | int | 链接超时最大时间单位秒,默认300秒 (60~600) |
| serialD | int | tcp/udp绑定的串口号(1~2) |

###### MQTT参数
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
| **字段** | **类型** | **含义** |
| --- | --- | --- |
| mqtt | str | 表示MQTT协议 |
| clentID | str | 自定义客户端ID，使用IMEI做客户端ID此处留空 |
| keepAlive | int | 客户端的keepalive超时值。 默认为60秒 |
| address | str | MQTT的地址或域名 |
| port | int | socket服务器的端口号 |
| cleanSession | int | MQTT是否保存会话标志位,0持久会话,1离线自动销毁 |
| Sub | str | 订阅主题 |
| pub | str | 发布主题 |
| qos | int | MQTT的QOS级别,默认0 |
| retain | int | MQTT的publish参数retain，默认0 |
| serialD | int | MQTT通道捆绑的串口ID (1~3) |

###### 阿里云参数
```
{
"protocol": "aliyun",
"type": "mos",
"keepAlive": "",
"clientID": "test_mos",
"Devicename": "light01",
"ProductKey": "a1QNbCDxIWM",
"DeviceSecret": "0bceb8010ade0df2e6989982e63f7601",
"ProductSecret": "",
"cleanSession": true,
"qos": "1",
"subscribe": {"0": "/a1QNbCDxIWM/light01/user/get"},
"publish": {"0": "/a1QNbCDxIWM/light01/user/update"},
"serialID": "1"
}
```
| **字段** | **类型** | **含义** |
| --- | --- | --- |
| aliyun | Str | 阿里云IOT的标识 |
| type | str | 一型一密tas/一机一密mos |
| keepAlive | int | 通信之间允许的最长时间段（以秒为单位）,默认为300，范围（60-1200）使用默认值就填""或者" " |
| clientID | str | clientID ,自定义字符（不超过64） |
| Devicename | str | 设备名称 |
| ProductKey | str | 产品密钥 |
| DeviceSecret | str | 设备密钥（使用一型一密认证此参数传入"") |
| ProductSecret | str | 产品密钥（使用一机一密认证时此参数传入"") |
| cleanSession | int | MQTT 保存会话标志位( 0则客户端是持久客户端，当客户端断开连接时，订阅信息和排队消息将被保留, 1代理将在其断开连接时删除有关此客户端的所有信息 ) |
| QOS | int | MQTT消息服务质量（默认0，可选择0或1）0：发送者只发送一次消息，不进行重试 1：发送者最少发送一次消息，确保消息到达Broker |
| subTopic | str | 订阅主题 |
| pubTopic | str | 发布主题 |
| serialD | int | MQTT通道捆绑的串口ID (1~3) |

###### 腾讯云参数
```
{
"protocol": "txyun",
"type": "mos",
"keepAlive": "",
"clientID": "test_tx_mos",
"Devicename": "Smart_test01",
"ProductKey": "H7MBLRYXN9",
"DeviceSecret": "89c7tXT3s3grZTr/YFjxSg==",
"ProductSecret": "",
"cleanSession": true,
"qos": "1",
"subscribe": {"0": "H7MBLRYXN9/Smart_test01/control"},
"publish": {"0": "H7MBLRYXN9/Smart_test01/event"},
"serialID": "1"
}
```
| **字段** | **类型** | **含义** |
| --- | --- | --- |
| txyun | str | 腾讯云IOT的标识 |
| type | str | 一型一密tas/一机一密mos |
| keepAlive | int | 通信之间允许的最长时间段（以秒为单位）,默认为300，范围（60-1200）使用默认值就填""或者" "。 |
| clientID | str | clientID ,自定义字符（不超过64） |
| Devicename | str | 设备名称 |
| ProductKey | str |
 |
| DeviceSecret | str | 设备密钥（使用一型一密认证此参数传入"") |
| ProductSecret | str | 产品密钥（使用一机一密认证时此参数传入"") |
| cleanSession | int | MQTT 保存会话标志位( 0则客户端是持久客户端，当客户端断开连接时，订阅信息和排队消息将被保留, 1代理将在其断开连接时删除有关此客户端的所有信息 ) |
| QOS | int | MQTT消息服务质量（默认0，可选择0或1）0：发送者只发送一次消息，不进行重试 1：发送者最少发送一次消息，确保消息到达Broker |
| subTopic | str | 订阅主题 |
| pubTopic | str | 发布主题 |
| serialD | int | MQTT通道捆绑的串口ID (1~3) |

## 设置APN

说明：这个指令只适合配置和使用不是同一张卡的场景

功能码: 0x60

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

`{"code": 0x60 , "status":1}`

| **字段** | **类型** | **含义** |
| --- | --- | --- |
| code | Str | 状态码 |
| data | str | set apn |
| success | int | 0 失败 1成功 |

## GPIO pins

功能码: 0x61

数据内容：
```
{"password": " ",
"data":{"pins":[
"pio2", -- 网路指示灯的GPIO (pio1~pio128)
"pio4", -- 与服务器连上后通知GPIO (pio1~pio128)
"pio4" -- 重置DTU参数的GPIO (pio1~pio128)
]}}
```
返回的数据内容：

`{"code": 0x61 , "status":1}`

| **字段** | **类型** | **含义** |
| --- | --- | --- |
| code | Str | 状态码 |
| data | str | set gpio pins |
| success | int | 0 失败 1成功 |

## OTA

功能码: 0x62

数据内容：
```
{"password": " ",
"data":{"ota":1
}
```
返回的数据内容：

`{"code": 0x62 , "status":1}`

| **字段** | **类型** | **含义** |
| --- | --- | --- |
| code | Str | 状态码 |
| data | str | OTA状态 |
| success | int | 0 失败 1成功 |

## 参数设置

功能码: 0x63

数据内容：
```
{"password": " ",
"data":{ 完整配置文件(省略)
}
```
返回的数据内容：

`{"code": 0x63 ,"status":1}`

| **字段** | **类型** | **含义** |
| --- | --- | --- |
| code | Str | 状态码 |
| data | dict | 完整的配置文件 |
| status | int | 0 失败 1成功 |