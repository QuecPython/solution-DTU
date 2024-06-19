## 修订历史

| Version | **Date**   | **Author** | **Change expression** |
| :------ | ---------- | ---------- | --------------------- |
| 1.0     | 2021-11-25 | 陈驰      | 初始版本                   |
| 1.1     | 2021-11-30 | 陈驰      | 增加对DTU配套组件和服务的描述 |
| 1.2     | 2022-01-14 | 陈驰      | 增加DTU代码和文档链接的描述 |

## DTU介绍

### DTU

- 英文全称Data Transfer Unit，数据传输单元。是专门用于将来自于设备端MCU的串口数据通过无线通信网络传送至服务器的无线终端设备。
- 业务逻辑：传感器采集数据发送给设备端MCU，设备端MCU通过串口将采集到的数据通过DTU发送到服务器；服务器接收到数据可以进行分析、处理、显示、保存等操作。

![DTU.png](./docs/media/DTU.png)

### RTU

- 英文全称Remote Terminal Unit，远程终端单元。
- 业务逻辑包括数据采集上报和远程指令控制两部分：
    - 数据采集上报：和DTU的数据采集上报功能完全一致
    - 远程指令控制：服务器下发控制指令，RTU接收到指令后，触发控制设备执行动作
- RTU功能 = DTU功能 + 控制单元。
- 下文中的DTU等同于RTU。

![RTU.png](./docs/media/RTU.png)

### 应用行业和场景

- 水利水电
- 矿产资源开发
- 地质灾害检测预警
- 环境保护
- 消防安全
- 市政管网等

![industry.png](./docs/media/industry.png)

## 移远DTU及其能力

### 产品线

|目前支持DTU的模组|
| --- |
| EC200U_CNLB |
| EC200U_EUAB |
| EC600U_CNLB |
| EC600U_CNLC |
| EC600N_CNLA |
| EC600N_CNLC |
| EC600S_CNLA |
| EC600S_CNLB |


### 产品能力

- **2个串口通道**
- **通道支持HTTP、TCP、UDP、MQTT、阿里云、腾讯云、移远云多种协议和云平台**
- **支持多个云端通道传输**
- **支持本地和远程参数配置**
- **支持OTA升级**
- **支持数据离线存储**
	- 在网络连接不稳定情况下，将发送失败的数据暂存至本地，在网络恢复后优先将本地数据发送至云端
	- 离线存储的数据量可通过配置文件配置
- **支持modbus协议**
- **支持命令模式和透传模式，方便不支持modbus协议的设备接入**
	- 命令模式下，支持对DTU的控制和参数读取；支持指定云端通道、指定MQTT主题，而非向所有的通道或主题推送同一个报文数据
	- 透传模式下，每个串口仅支持单通道透传，但支持指定MQTT主题
- **支持常用的传感器、执行单元和输入设备**
	- 传感器：
		- 照度传感器（BH1750、OPT3001、GL5516、GL5528）
		- 三轴加速度传感器（ADXL346、BMA250、LIS2DH12TR）
		- 温湿度传感器（HDC1080、HDC2080、AHT10、DHT11）
		- 可燃气体传感器
		- CO2气体传感器
		- GNSS定位模块
		- ...
	
	- 执行单元：
		- 功放
		- 电机
		- LED
		- LCD（ILI9225、ST7735、ST7789、SSD1306、UC1628）
		- ...
	
	- 输入设备：
		- 麦克风
		- 摄像头（GC032A、BF3901）
		- 矩阵键盘
		- ...
- **支持QuecPython，可以使用Python代码快速实现二次开发**
- **开放了GPIO、SPI、IIC、PWM等各种外设接口，方便外设扩充**

### 产品配套组件和服务

我司DTU产品的配套组件和服务是为了更好地支持基于DTU的终端产品的原型验证和功能开发。

#### 板载资源丰富的QuecPython开发板

我司的QuecPython开发板的板载资源丰富，支持照度传感器、温湿度传感器、喇叭接口、咪头接口、三色LED灯、LCD屏接口、Camera接口，及其它丰富的外设接口，配合下节将提及的GUI工具，可在QuecPython开发板上进行终端产品的原型验证。

![](./docs/media/dev_board.png)

#### 强大的上位机GUI工具

针对DTU所有的单元功能，GUI均提供了对应的交互入口，用于通过PC调试DTU，可作为终端产品开发前的快速原型验证。

[点此下载DTU GUI工具。](https://python.quectel.com/download)

![](./docs/media/gui_get_imei.png)

#### QPYcom工具

QPYcom工具是一个集**QuecPython repl交互、PC和模组间文件传输、文件系统镜像制作并打包到固件包、及固件烧录等各种功能**于一体的强大利器。

用户如需进行DTU的二次开发，使用QPYcom将会大大提高开发的效率。

[点此下载QPYCom工具。](https://python.quectel.com/download)

QPYCom的使用文档，参见安装目录下的`docs`文件夹。

![](./docs/media/QPYCom_V1.8.png)

#### 线上生成配置文件

通过我司的DTU服务平台，用户只需要点击按钮或填写必要参数值，即可在线上快速生成配置文件，并支持导出到本地、和给DTU进行配置文件的在线升级。

该功能尚在开发中，即将上线。

### 产品优势

- **增加了命令模式，设备端可在该模式下控制DTU的行为，亦可主动向DTU推送数据**

- **支持网页生成DTU配置文件（即将上线）**

- **支持上位机GUI工具，快速实现设备开发的原型验证**

- **支持云端通道选择与MQTT topic选择**
	
	- 在命令模式下，DTU支持向指定云端通道发送数据，而非向所有通道同时推送数据，可节省流量及减少垃圾数据产生
	- MQTT、阿里云与腾讯云类型通道支持topic选择，DTU可支持向指定的topic发布数据
	- 通道可绑定串口，绑定串口后仅会向绑定的串口发送数据
	
- **透传时增加校验机制，保证上传数据的正确性**
	
	- 与串口通信双重校验机制，同时校验数据长度与CRC32
	- 校验失败重发机制，发送失败时可自动重发
	
- **modbus模式和命令模式自适应，用户直接进行通信即可**

- **RTU可直接做主控，摒弃MCU，降低软硬件开发成本**
	
	- RTU可直接作为主控，省去MCU及其周边电路，降低硬件成本
  
	  ![Reduce_Hardware_Costs.png](./docs/media/Reduce_Hardware_Costs.png)
	
  - 可使用Python进行二次开发，降低软件开发成本
    
    ![C2Py.png](./docs/media/C2Py.png)
	  
	- 我司多平台模组适用，使用Python开发，无需修改代码即可快速切换至不同模组
	
- **业务功能扩充方便**
	- 开放了GPIO、SPI、IIC、PWM等各种外设接口，方便外设扩充
	
- **强大的客户服务和技术支持能力**

## 移远DTU的工作原理

### 命令模式

![CMD_Mode_Working_Principle.png](./docs/media/CMD_Mode_Working_Principle.png)

### 透传模式

![Transparent_Mode_Working_Principle.png](./docs/media/Transparent_Mode_Working_Principle.png)

### modbus模式

modbus模式下，严格遵守modbus协议规范，且遵守modbus协议的DTU产品在行业内的应用规则：DTU作为主机，根据用户配置，周期性向从机设备索要数据，推送至云端。

## DTU代码下载和使用文档

### 代码下载

`git clone https://gitee.com/qpy-solutions/dtu.git`
或
`git clone git@gitee.com:qpy-solutions/dtu.git`

### 使用文档

- DTU产品介绍：[点此进入][1]
- DTU用户指导：[点此进入][2]
- DTU协议规范：[点此进入][3]
- DTU上位机工具用户指导：[点此进入][4]


  [1]: https://python.quectel.com/doc/doc/Product_case/zh/dtu/DTU_Product_Introduction.html
  [2]: https://python.quectel.com/doc/doc/Product_case/zh/dtu/DTU_User_Guides.html
  [3]: https://python.quectel.com/doc/doc/Product_case/zh/dtu/DTU_Protocol_Specification.html
  [4]: https://python.quectel.com/doc/doc/Product_case/zh/dtu/DTU_GUI_User_Guides.html
  