## 1. DTU和RTU的概念

### 1.1 DTU

- 英文全称Data Transfer Unit，数据传输单元。是专门用于将来自于设备端MCU的串口数据通过无线通信网络传送至服务器的无线终端设备。
- 业务逻辑：传感器采集数据发送给设备端MCU，设备端MCU通过串口将采集到的数据通过DTU发送到服务器；服务器接收到数据可以进行分析、处理、显示、保存等操作。

![image_1fl8ad0ct150a195i169m1hk2i3g33.png-40.8kB][1]

### 1.2 RTU

- 英文全称Remote Terminal Unit，远程终端单元。
- 业务逻辑包括数据采集上报和远程指令控制两部分：
    - 数据采集上报：和DTU的数据采集上报功能完全一致
    - 远程指令控制：服务器下发控制指令，RTU接收到指令后，触发控制设备执行动作
- RTU功能 = DTU功能 + 控制单元。

![image_1fl8bn24285j2a23qrvd5pcd29.png-33.4kB][2]

### 1.3 应用行业和场景

- 水利水电
- 矿产资源开发
- 地质灾害检测预警
- 环境保护
- 消防安全
- 市政管网等

![image_1fl8i96dc1kheeb5109pb281mjs2j.png-99kB][3]

## 2. 移远DTU及其能力

### 2.1 产品线

目前支持DTU的模组列表：

- EC200U_CNLB
- EC200U_EUAB
- EC600U_CNLB
- EC600U_CNLC
- EC600N_CNLA
- EC600N_CNLC
- EC600S_CNLA
- EC600S_CNLB

### 2.2 产品能力

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
	- 命令模式下，支持对DTU的控制和参数读取；对比友商的DTU，我司的DTU支持指定云端通道、指定MQTT主题，而非向所有的通道或主题推送同一个报文数据
	- 透传模式下，每个串口仅支持单通道透传，但对比友商的DTU，我司的DTU仍然支持指定MQTT主题

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

### 2.3 产品优势

- **支持网页生成DTU配置文件（即将上线）**

- **支持云端通道选择与MQTT topic选择**
	- 在命令模式下，DTU支持向指定云端通道发送数据，可节省流量及减少垃圾数据产生
	- MQTT、阿里云与腾讯云类型通道支持topic选择，DTU可支持向指定的topic发布数据
	- 通道可绑定串口，绑定串口后仅会向绑定的串口发送数据

- **透传时增加校验机制，保证上传数据的正确性**
	- 与串口通信双重校验机制，同时校验数据长度与CRC32
	- 校验失败重发机制，发送失败时可自动重连

- **modbus模式和命令模式自适应，用户直接进行通信即可**

- **RTU可直接做主控，摒弃MCU，降低软硬件开发成本**
	- RTU可直接作为主控，省去MCU及其周边电路，降低硬件成本

    ![image_1fl87kl5c1f6p1t3c26ahga7951s.png-39.9kB][4]

	- 使用Python开发，降低软件开发成本

    ![image_1fl8c92841mic1r8d1r0h177i8qs2m.png-13.5kB][5]
    
	- 我司多平台模组适用，使用Python开发，无需修改代码即可快速切换至不同模组

- **业务功能扩充方便**
	- 开放了GPIO、SPI、IIC、PWM等各种外设接口，方便外设扩充
	
- **强大的客户服务和技术支持能力**

## 3. 移远DTU的工作原理

### 3.1 命令模式

![image_1fl8lu3af1tgmgoruqeofq15qof1.png-139.4kB][6]

### 3.2 透传模式

![image_1fl8lh3nn1kmbullse416vq105nbu.png-92.6kB][7]

## 4. 附件链接


  [1]: http://static.zybuluo.com/chenchi/pinotn6ajcibu0rgo122vvj0/image_1fl8ad0ct150a195i169m1hk2i3g33.png
  [2]: http://static.zybuluo.com/chenchi/0312gv62wstwsh1mfgdz2g6m/image_1fl8bn24285j2a23qrvd5pcd29.png
  [3]: http://static.zybuluo.com/chenchi/6vkjl7repti62n6eonpc3d55/image_1fl8i96dc1kheeb5109pb281mjs2j.png
  [4]: http://static.zybuluo.com/chenchi/kovfl64tqfzp4alalml14rf9/image_1fl87kl5c1f6p1t3c26ahga7951s.png
  [5]: http://static.zybuluo.com/chenchi/ucyn1otc6oj1yib97bz45loi/image_1fl8c92841mic1r8d1r0h177i8qs2m.png
  [6]: http://static.zybuluo.com/chenchi/8h3rkym31o6hjdurnmtcuw26/image_1fl8lu3af1tgmgoruqeofq15qof1.png
  [7]: http://static.zybuluo.com/chenchi/70f0is2vbkla2q5tgunykvl8/image_1fl8lh3nn1kmbullse416vq105nbu.png