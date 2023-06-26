import zlib
import threading, time, wx, re
import json
import serial.tools.list_ports
from pubsub import pub
import os, base64
from cloud_config import CloudConfig
from datetime import datetime
from location import chinese_map, english_map

ser = serial.Serial()  # 创建串口对象
serPort = serial.tools.list_ports  # 串口列表
serialStatus = False
add_time = False  # 是否加时间戳
convet_to_hex = False  # 是否转为hex
serialList = []  # 串口列表
label_list = []  # 云配置标签
basic_setting_funcode = ["50", "51", "52", "53", "54", "55", "56", "57", "58", "59", "60", "61", "62", "63",] # 设置参数指令
serial_read_buffer = ""

# 语言
LANGUAGE = 'chinese'  # english


class dtu_gui_frame(wx.Frame):

    def __init__(self, *args, **kwds):
        self.__dtu_config = dict()

        kwds["style"] = kwds.get("style", 0) | wx.DEFAULT_FRAME_STYLE
        wx.Frame.__init__(self, *args, **kwds)
        self.cloud_config = CloudConfig()
        self.SetSize((1000, 710))

        # Menu
        self.menu = wx.Menu()
        cn_item = self.menu.Append(wx.ID_ABOUT, "中文")
        self.menu.AppendSeparator()
        en_item = self.menu.Append(wx.ID_EXIT, "English")
        # Menu Bar
        self.frame_menubar = wx.MenuBar()
        self.frame_menubar.Append(self.menu, "语言")
        self.SetMenuBar(self.frame_menubar)

        self.Bind(wx.EVT_MENU, self.SetChinese, cn_item)
        self.Bind(wx.EVT_MENU, self.SetEnglish, en_item)

        self.SetTitle("DTU Tools")

        self.SetBackgroundColour(wx.NullColour)
        bc = self.GetBackgroundColour()

        # 串口配置页面
        self.uart_connect_page()

        self.main_page_init()

        self.__do_layout()

        self.Bind(wx.EVT_COMBOBOX, self.cloud_interface_change, self.cloud_type_combo_box)

        # serial rcv data timer
        self.ser_recv_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.ser_rcv_handler, self.ser_recv_timer)
        # msg for update ui form
        pub.subscribe(self.update_serial_port_display, "uiUpdate")

        # 打开串口按钮
        self.Bind(wx.EVT_BUTTON, self.open_serial, self.enable_uart_button)
        # 打开配置界面，并读取DTU当前配置
        self.Bind(wx.EVT_BUTTON, self.open_setting_config, self.get_now_setting_button)

        # 清空输入框、输出框、命令框
        self.Bind(wx.EVT_BUTTON, self.clear_data, self.clear_recv_button)
        self.Bind(wx.EVT_BUTTON, self.clear_data, self.clear_send_button)
        self.Bind(wx.EVT_BUTTON, self.clear_data, self.clear_button)

        # 查询DTU信息、设置重启
        #self.Bind(wx.EVT_BUTTON, self.query_command_handle, self.get_now_setting_button)
        self.Bind(wx.EVT_BUTTON, self.retore_factory_setting, self.restore_factory_setting_button)
        self.Bind(wx.EVT_BUTTON, self.query_command_handle, self.query_imei_button)
        self.Bind(wx.EVT_BUTTON, self.query_command_handle, self.query_phone_num_button)
        self.Bind(wx.EVT_BUTTON, self.query_command_handle, self.query_signal_strength_button)
        self.Bind(wx.EVT_BUTTON, self.dtu_restart, self.restart_button)

        # 配置DTU参数
        self.Bind(wx.EVT_BUTTON, self.save_config_param, self.save_setting_button)

        # 串口发送数据
        self.Bind(wx.EVT_BUTTON, self.send_data, self.send_button)

    def SetChinese(self, event):
        global LANGUAGE
        LANGUAGE = 'chinese'
        self.__set_language(LANGUAGE)
        self.Layout()

    def SetEnglish(self, event):
        global LANGUAGE
        LANGUAGE = 'english'
        self.__set_language(LANGUAGE)
        self.Layout()

    def __set_language(self, language):
        self.Destroy_Window()
        self.clear_label_list()

        if language == 'chinese':
            items = chinese_map.items()
            self.frame_menubar.SetMenuLabel(0, '语言')
            self.main_page.SetPageText(0, '交互')
            self.main_page.SetPageText(1, '参数配置')
            if ser.isOpen():
                self.enable_uart_button.SetLabel('关闭串口')
            else:
                self.enable_uart_button.SetLabel('打开串口')
        else:
            items = english_map.items()
            self.frame_menubar.SetMenuLabel(0, 'language')
            self.main_page.SetPageText(0, 'repl')
            self.main_page.SetPageText(1, 'settings')
            if ser.isOpen():
                self.enable_uart_button.SetLabel('close serial')
            else:
                self.enable_uart_button.SetLabel('open serial')

        for k, v in items:
            attr = getattr(self, k, None)
            if attr is None:
                continue

            if isinstance(attr, (wx.Button, wx.StaticText)):
                attr.SetLabel(v)

            if isinstance(attr, wx.ComboBox):
                for index, string in enumerate(v):
                    attr.SetString(index, string)

    def uart_connect_page(self):
        self.uart_port_list_combo_box = wx.ComboBox(self, wx.ID_ANY, choices=[""], style=wx.CB_DROPDOWN)
        self.uart_bautrate_combo_box = wx.ComboBox(self, wx.ID_ANY,
                                        choices=["1200", "2400", "4800", "9600", "14400", "19200", "28800", "38400",
                                                "57600", "115200", "230400", "460800", "921600"], style=wx.CB_READONLY)
        self.uart_bit_len_combo_box = wx.ComboBox(self, wx.ID_ANY, choices=["7", "8"], style=wx.CB_READONLY)
        self.uart_parity_combo_box = wx.ComboBox(self, wx.ID_ANY, choices=["NONE", "ODD", "EVENT"], style=wx.CB_READONLY)
        self.uart_stop_big_combo_box = wx.ComboBox(self, wx.ID_ANY, choices=["1", "2"], style=wx.CB_READONLY)
        self.enable_uart_button = wx.Button(self, wx.ID_ANY, u"打开串口")

        # 设置属性
        self.uart_port_list_combo_box.SetToolTip("Uart List")
        self.uart_port_list_combo_box.SetMinSize((176, 20))
        self.uart_bautrate_combo_box.SetMinSize((70, 20))
        self.uart_bautrate_combo_box.SetSelection(9) # 设置选择框默认选择值
        self.uart_bit_len_combo_box.SetMinSize((40, 20))
        self.uart_bit_len_combo_box.SetSelection(1)
        self.uart_parity_combo_box.SetMinSize((65, 20))
        self.uart_parity_combo_box.SetSelection(0)
        self.uart_stop_big_combo_box.SetMinSize((40, 20))
        self.uart_stop_big_combo_box.SetSelection(0)
        self.enable_uart_button.SetMinSize((86, 25))
        

        # 设置sizer
        self.uart_config_page_main_page = wx.BoxSizer(wx.HORIZONTAL) # 水平
        sizer_31 = wx.BoxSizer(wx.VERTICAL) # 垂直
        sizer_32 = wx.BoxSizer(wx.HORIZONTAL)
        self.label_6 = wx.StaticText(self, wx.ID_ANY, u"【PC端口参数】")
        sizer_32.Add(self.label_6, 0, 0, 0)
        sizer_32.Add((20, 20), 0, 0, 0)
        self.label_7 = wx.StaticText(self, wx.ID_ANY, u"串口")
        self.label_7.SetMinSize((41, 15))
        sizer_32.Add(self.label_7, 0, 0, 0)
        sizer_32.Add(self.uart_port_list_combo_box, 0, 0, 0)
        sizer_32.Add((20, 20), 0, 0, 0)
        self.label_8 = wx.StaticText(self, wx.ID_ANY, u"波特率")
        sizer_32.Add(self.label_8, 0, 0, 0)
        sizer_32.Add((20, 20), 0, 0, 0)
        sizer_32.Add(self.uart_bautrate_combo_box, 0, 0, 0)
        sizer_32.Add((20, 20), 0, 0, 0)
        self.label_9 = wx.StaticText(self, wx.ID_ANY, u"数据位/校验位/停止位")
        sizer_32.Add(self.label_9, 0, 0, 0)
        sizer_32.Add((20, 20), 0, 0, 0)
        sizer_32.Add(self.uart_bit_len_combo_box, 0, 0, 0)
        sizer_32.Add(self.uart_parity_combo_box, 0, 0, 0)
        sizer_32.Add(self.uart_stop_big_combo_box, 0, 0, 0)
        sizer_32.Add((20, 20), 0, 0, 0)
        sizer_32.Add(self.enable_uart_button, 0, 0, 0)
        sizer_32.Add((20, 20), 0, 0, 0)
        
        sizer_31.Add((20, 5), 0, 0, 0)
        sizer_31.Add(sizer_32, 1, wx.EXPAND, 0)
        sizer_31.Add((20, 5), 0, 0, 0)
        self.uart_config_page_main_page.Add(sizer_31, 1, wx.EXPAND, 0)

    def main_page_init(self):
        self.main_page = wx.Notebook(self, wx.ID_ANY)
        self.interact_page_init()
        self.setting_config_init()
        # 主页增加交互页
        self.main_page.AddPage(self.interact_page, u"交互")
        self.main_page.AddPage(self.setting_config_page, u"参数配置")
    
    # 参数配置
    def setting_config_init(self):
        self.setting_config_page = wx.Panel(self.main_page, wx.ID_ANY)
        #基本参数
        self.cloud_type_combo_box = wx.ComboBox(self.setting_config_page, wx.ID_ANY, pos=(120, 30),
                                choices=[u"阿里云", u"腾讯云", u"华为云", u"移远云", u"TCP私有云", u"MQTT私有云"], style=wx.CB_READONLY)
        self.fota_combo_box = wx.ComboBox(self.setting_config_page, wx.ID_ANY, choices=[u"关闭", u"开启"], style=wx.CB_READONLY)
        self.sota_combo_box = wx.ComboBox(self.setting_config_page, wx.ID_ANY, choices=[u"关闭", u"开启"], style=wx.CB_READONLY)
        self.offline_storage_combo_box = wx.ComboBox(self.setting_config_page, wx.ID_ANY, choices=[u"关闭", u"开启"], style=wx.CB_READONLY)
        # 串口参数
        self.uart_port_num_combo_box = wx.ComboBox(self.setting_config_page, wx.ID_ANY, choices=["0", "1", "2"], style=wx.CB_READONLY)
        choices = ["1200", "2400", "4800", "9600", "14400", "19200", "28800", "38400", "57600", "115200", "230400",
                   "460800", "921600"]
        choices1 = ["NONE", "ODD", "EVENT"]
        self.uart_baudrate_combo_box = wx.ComboBox(self.setting_config_page, wx.ID_ANY, choices=choices, style=wx.CB_READONLY)
        self.uart_databits_combo_box = wx.ComboBox(self.setting_config_page, wx.ID_ANY, choices=["7", "8"], style=wx.CB_READONLY)
        self.uart_parity_combo_box = wx.ComboBox(self.setting_config_page, wx.ID_ANY, choices=choices1, style=wx.CB_READONLY)
        self.uart_stopbits_combo_box = wx.ComboBox(self.setting_config_page, wx.ID_ANY, choices=["1", "2"], style=wx.CB_READONLY)
        self.uart_flowctl_combo_box = wx.ComboBox(self.setting_config_page, wx.ID_ANY, choices=["FC_NONE", "FC_HW"], style=wx.CB_READONLY)
        self.rs485_direction_pin_txt_ctrl = wx.TextCtrl(self.setting_config_page, wx.ID_ANY, "")
        self.filter_txt_ctrl = wx.TextCtrl(self.setting_config_page, wx.ID_ANY, "")
        # 设置属性
        self.uart_port_num_combo_box.SetSelection(2)
        self.cloud_type_combo_box.SetMinSize((130, 30))
        self.cloud_type_combo_box.SetSelection(0) # 设置选择框默认选择值
        self.fota_combo_box.SetMinSize((90, 30))
        self.fota_combo_box.SetSelection(1)
        self.sota_combo_box.SetMinSize((90, 30))
        self.sota_combo_box.SetSelection(1)
        self.offline_storage_combo_box.SetMinSize((90, 30))
        self.offline_storage_combo_box.SetSelection(1)
        self.uart_port_num_combo_box.SetMinSize((90, 30))
        self.uart_baudrate_combo_box.SetMinSize((90, 30))
        self.uart_baudrate_combo_box.SetSelection(9)
        self.uart_databits_combo_box.SetMinSize((90, 30))
        self.uart_databits_combo_box.SetSelection(1)
        self.uart_parity_combo_box.SetMinSize((90, 30))
        self.uart_parity_combo_box.SetSelection(0)
        self.uart_stopbits_combo_box.SetMinSize((90, 30))
        self.uart_stopbits_combo_box.SetSelection(0)
        self.uart_flowctl_combo_box.SetMinSize((90, 30))
        self.uart_flowctl_combo_box.SetSelection(0)
        self.rs485_direction_pin_txt_ctrl.SetMinSize((90, 30))
        self.filter_txt_ctrl.SetMinSize((90, 30))

        # sizer
        setting_sizer1 = wx.BoxSizer(wx.HORIZONTAL) # 水平
        setting_uart_sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        setting_uart_sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        setting_sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        setting_sizer4 = wx.BoxSizer(wx.HORIZONTAL)
        setting_sizer5 = wx.BoxSizer(wx.HORIZONTAL)
        setting_sizer6 = wx.BoxSizer(wx.HORIZONTAL)
        self.setting_mian_sizer = wx.BoxSizer(wx.VERTICAL)

        setting_sizer1.Add((20, 0), 0, 0, 0)
        self.cloud_type_txt = wx.StaticText(self.setting_config_page, wx.ID_ANY, u"云平台通信类型")
        setting_sizer1.Add(self.cloud_type_txt, 0, 0, 0)
        setting_sizer1.Add((65, 20), 0, 0, 0)
        setting_sizer1.Add(self.cloud_type_combo_box, 0, 0, 0)

        setting_sizer3.Add((20, 0), 0, 0, 0)
        self.fota_txt = wx.StaticText(self.setting_config_page, wx.ID_ANY, u"固件升级")
        setting_sizer3.Add(self.fota_txt, 0, 0, 0)
        setting_sizer3.Add((101, 20), 0, 0, 0)
        setting_sizer3.Add(self.fota_combo_box, 0, 0, 0)

        setting_sizer3.Add((85, 0), 0, 0, 0)
        self.sota_txt = wx.StaticText(self.setting_config_page, wx.ID_ANY, u"脚本升级")
        setting_sizer3.Add(self.sota_txt, 0, 0, 0)
        setting_sizer3.Add((20, 20), 0, 0, 0)
        setting_sizer3.Add(self.sota_combo_box, 0, 0, 0)

        setting_sizer4.Add((20, 0), 0, 0, 0)
        self.filter_txt = wx.StaticText(self.setting_config_page, wx.ID_ANY, u"透传数据过滤设置")
        setting_sizer4.Add(self.filter_txt, 0, 0, 0)
        setting_sizer4.Add((52, 20), 0, 0, 0)
        setting_sizer4.Add(self.filter_txt_ctrl, 0, 0, 0)

        setting_sizer5.Add((20, 0), 0, 0, 0)
        self.history_txt = wx.StaticText(self.setting_config_page, wx.ID_ANY, u"历史数据存储")
        setting_sizer5.Add(self.history_txt, 0, 0, 0)
        setting_sizer5.Add((78, 20), 0, 0, 0)
        setting_sizer5.Add(self.offline_storage_combo_box, 0, 0, 0)
        
        setting_uart_sizer1.Add((20, 0), 0, 0, 0)
        self.uart_config_txt = wx.StaticText(self.setting_config_page, wx.ID_ANY, u"串口参数配置")
        setting_uart_sizer1.Add(self.uart_config_txt, 0, 0, 0)
        setting_uart_sizer1.Add((65, 0), 0, 0, 0)

        self.uart_port_txt = wx.StaticText(self.setting_config_page, wx.ID_ANY, u"串口号")
        setting_uart_sizer1.Add(self.uart_port_txt, 0, 0, 0)
        setting_uart_sizer1.Add((20, 20), 0, 0, 0)
        setting_uart_sizer1.Add(self.uart_port_num_combo_box, 0, 0, 0)

        setting_uart_sizer1.Add((40, 0), 0, 0, 0)
        self.baudrate_txt = wx.StaticText(self.setting_config_page, wx.ID_ANY, u"波特率")
        setting_uart_sizer1.Add(self.baudrate_txt, 0, 0, 0)
        setting_uart_sizer1.Add((20, 20), 0, 0, 0)
        setting_uart_sizer1.Add(self.uart_baudrate_combo_box, 0, 0, 0)

        setting_uart_sizer1.Add((40, 0), 0, 0, 0)
        self.databits_txt = wx.StaticText(self.setting_config_page, wx.ID_ANY, u"数据位")
        setting_uart_sizer1.Add(self.databits_txt, 0, 0, 0)
        setting_uart_sizer1.Add((20, 20), 0, 0, 0)
        setting_uart_sizer1.Add(self.uart_databits_combo_box, 0, 0, 0)

        setting_uart_sizer1.Add((40, 0), 0, 0, 0)
        self.parity_txt = wx.StaticText(self.setting_config_page, wx.ID_ANY, u"校验位")
        setting_uart_sizer1.Add(self.parity_txt, 0, 0, 0)
        setting_uart_sizer1.Add((20, 20), 0, 0, 0)
        setting_uart_sizer1.Add(self.uart_parity_combo_box, 0, 0, 0)
        
        setting_uart_sizer2.Add((155, 0), 0, 0, 0)
        self.stopbits_txt = wx.StaticText(self.setting_config_page, wx.ID_ANY, u"停止位")
        setting_uart_sizer2.Add(self.stopbits_txt, 0, 0, 0)
        setting_uart_sizer2.Add((20, 20), 0, 0, 0)
        setting_uart_sizer2.Add(self.uart_stopbits_combo_box, 0, 0, 0)

        setting_uart_sizer2.Add((40, 0), 0, 0, 0)
        self.flowctl_txt = wx.StaticText(self.setting_config_page, wx.ID_ANY, u"流控")
        setting_uart_sizer2.Add(self.flowctl_txt, 0, 0, 0)
        setting_uart_sizer2.Add((20, 20), 0, 0, 0)
        setting_uart_sizer2.Add(self.uart_flowctl_combo_box, 0, 0, 0)

        setting_uart_sizer2.Add((40, 0), 0, 0, 0)
        self.rs485_pin_txt = wx.StaticText(self.setting_config_page, wx.ID_ANY, u"控制485通信方向Pin")
        setting_uart_sizer2.Add(self.rs485_pin_txt, 0, 0, 0)
        setting_uart_sizer2.Add((20, 20), 0, 0, 0)
        setting_uart_sizer2.Add(self.rs485_direction_pin_txt_ctrl, 0, 0, 0)

        setting_sizer6.Add((20, 0), 0, 0, 0)
        self.yun_config_txt = wx.StaticText(self.setting_config_page, wx.ID_ANY, u"云参数配置---------------------")
        setting_sizer6.Add(self.yun_config_txt, 0, 0, 0)

        self.setting_mian_sizer.Add((0, 5), 0, 0, 0)
        self.setting_mian_sizer.Add(setting_sizer1, 0, wx.EXPAND, 0)
        self.setting_mian_sizer.Add((0, 5), 0, 0, 0)
        self.setting_mian_sizer.Add(setting_sizer3, 0, wx.EXPAND, 0)
        self.setting_mian_sizer.Add((0, 5), 0, 0, 0)
        self.setting_mian_sizer.Add(setting_sizer4, 0, wx.EXPAND, 0)
        self.setting_mian_sizer.Add((0, 5), 0, 0, 0)
        self.setting_mian_sizer.Add(setting_sizer5, 0, wx.EXPAND, 0)
        self.setting_mian_sizer.Add((0, 5), 0, 0, 0)
        self.setting_mian_sizer.Add(setting_uart_sizer1, 0, wx.EXPAND, 0)
        self.setting_mian_sizer.Add((0, 5), 0, 0, 0)
        self.setting_mian_sizer.Add(setting_uart_sizer2, 0, wx.EXPAND, 0)
        self.setting_mian_sizer.Add((0, 5), 0, 0, 0)
        self.setting_mian_sizer.Add(setting_sizer6, 0, wx.EXPAND, 0)
        self.setting_config_page.SetSizer(self.setting_mian_sizer)

    def interact_page_init(self):
        self.interact_page = wx.Panel(self.main_page, wx.ID_ANY)
        self.fileSplitter = wx.SplitterWindow(self.interact_page, wx.ID_ANY)
        self.fileSplitter.SetSashGravity(0.5)
        self.command_display_page = wx.Panel(self.fileSplitter, wx.ID_ANY)
        self.serial_data_page = wx.Panel(self.fileSplitter, wx.ID_ANY)
        # 串口数据显示界面
        self.clear_recv_button = wx.Button(self.serial_data_page, 1000, u"清空")
        # self.clear_recv_button.SetBackgroundColour((240, 240, 240, 255))
        self.uart_data_display = wx.TextCtrl(self.serial_data_page, wx.ID_ANY, "", style=wx.TE_MULTILINE)
        # 串口发送数据
        self.clear_send_button = wx.Button(self.serial_data_page, 1001, u"清空发送")
        self.send_button = wx.Button(self.serial_data_page, wx.ID_ANY, u"发送")
        self.uart_send_display = wx.TextCtrl(self.serial_data_page, wx.ID_ANY, "")

        # 工具交互界面
        self.command_display = wx.TextCtrl(self.command_display_page, wx.ID_ANY, "", style=wx.TE_MULTILINE)
        self.clear_button = wx.Button(self.command_display_page, 1002, u"清空")
        self.get_now_setting_button = wx.Button(self.command_display_page, 2000, u"获取当前参数") # 获取当前参数
        self.save_setting_button = wx.Button(self.command_display_page, 2001, u"保存所有设置参数并重启") # 保存所有参数
        self.restore_factory_setting_button = wx.Button(self.command_display_page, 2002, u"恢复出厂参数设置并重启") # 恢复出厂参数设置并重启
        self.query_imei_button = wx.Button(self.command_display_page, 2003, u"查询IMEI") # 查询IMEI
        self.query_phone_num_button = wx.Button(self.command_display_page, 2004, u"查询本机号码") # 查询本机号码
        self.query_signal_strength_button = wx.Button(self.command_display_page, 2005, u"查询信号强度") # 查询信号强度
        self.restart_button = wx.Button(self.command_display_page, 2006, u"设备重启")# 设备重启
        
        # 设置属性
        self.uart_data_display.SetMinSize((500, 350))
        self.uart_send_display.SetMinSize((500, 100))
        self.command_display.SetMinSize((500, 350))
        self.clear_recv_button.SetMinSize((80, 30))
        self.clear_send_button.SetMinSize((80, 30))
        self.send_button.SetMinSize((80, 30))
        self.clear_button.SetMinSize((80, 30))
        self.get_now_setting_button.SetMinSize((200, 30))
        self.save_setting_button.SetMinSize((200, 30))
        self.restore_factory_setting_button.SetMinSize((200, 30))
        self.query_imei_button.SetMinSize((90, 30))
        self.query_phone_num_button.SetMinSize((90, 30))
        self.query_signal_strength_button.SetMinSize((90, 30))
        self.restart_button.SetMinSize((90, 30))

        # 设置sizer
        self.interact_page_main_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.command_page_sizer = wx.BoxSizer(wx.VERTICAL)
        self.interact_page_sizer = wx.BoxSizer(wx.VERTICAL)
        recv_button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        send_button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        origin_button_sizer = wx.BoxSizer(wx.HORIZONTAL)

        sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer3 = wx.BoxSizer(wx.HORIZONTAL)
        # 接收相关按钮 清空接收
        recv_button_sizer.Add((20, 20), 0, wx.ALIGN_CENTER_VERTICAL, 0)
        recv_button_sizer.Add(self.clear_recv_button, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        # 发送相关按钮 HEX、清空发送、发送
        send_button_sizer.Add((20, 20), 0, wx.ALIGN_CENTER_VERTICAL, 0)
        send_button_sizer.Add(self.clear_send_button, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        send_button_sizer.Add((20, 20), 0, wx.ALIGN_CENTER_VERTICAL, 0)
        send_button_sizer.Add(self.send_button, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        
        # 左侧框
        self.interact_page_sizer.Add(self.uart_data_display, 0, 0, 0) # 接收数据框
        self.interact_page_sizer.Add((0, 10), 0, 0, 0)
        self.interact_page_sizer.Add(recv_button_sizer, 0, 0, 0)
        self.interact_page_sizer.Add((0, 30), 0, 0, 0)
        self.interact_page_sizer.Add(self.uart_send_display, 0, 0, 0) # 发送数据框
        self.interact_page_sizer.Add((0, 10), 0, 0, 0)
        self.interact_page_sizer.Add(send_button_sizer, 0, 0, 0)
        self.serial_data_page.SetSizer(self.interact_page_sizer)
        # 右侧框
        sizer1.Add((20, 0), 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer1.Add(self.get_now_setting_button, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer1.Add((20, 0), 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer1.Add(self.save_setting_button, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer2.Add((20, 0), 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer2.Add(self.restore_factory_setting_button, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer3.Add((20, 0), 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer3.Add(self.query_imei_button, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer3.Add((20, 0), 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer3.Add(self.query_phone_num_button, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer3.Add((20, 0), 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer3.Add(self.query_signal_strength_button, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer3.Add((20, 0), 0, wx.ALIGN_CENTER_VERTICAL, 0)
        sizer3.Add(self.restart_button, 0, wx.ALIGN_CENTER_VERTICAL, 0)

        origin_button_sizer.Add((400, 20), 0, 0, 0)
        origin_button_sizer.Add(self.clear_button, 0, 0, 0)

        self.command_page_sizer.Add((0, 20), 0, 0, 0)
        self.command_page_sizer.Add(sizer1, 0, 0, 0)
        self.command_page_sizer.Add((0, 20), 0, 0, 0)
        self.command_page_sizer.Add(sizer2, 0, 0, 0)
        self.command_page_sizer.Add((0, 20), 0, 0, 0)
        self.command_page_sizer.Add(sizer3, 0, 0, 0)
        self.command_page_sizer.Add((0, 20), 0, 0, 0)
        self.command_page_sizer.Add(self.command_display, 1, wx.EXPAND, 0) # 原始数据框
        self.command_page_sizer.Add((0, 10), 0, 0, 0)
        self.command_page_sizer.Add(origin_button_sizer, 1, wx.EXPAND, 0)
        self.command_display_page.SetSizer(self.command_page_sizer)
        
        self.fileSplitter.SplitVertically(self.serial_data_page, self.command_display_page)
        self.interact_page_main_sizer.Add(self.fileSplitter, 1, wx.EXPAND, 0)
        self.interact_page.SetSizer(self.interact_page_main_sizer)
        self.interact_page.SetBackgroundColour((240, 240, 240, 255))

    def __do_layout(self):
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        main_sizer.Add(self.uart_config_page_main_page, 0, wx.EXPAND, 0)    # 串口连接参数
        main_sizer.Add((20, 15), 0, 0, 0)
        main_sizer.Add(self.main_page, 0, wx.EXPAND, 0) # 主界面

        self.SetSizer(main_sizer)
        self.Layout()

    # 销毁页面
    def Destroy_Window(self):
        for i in eval("label_list"):
            i.Destroy()

    def clear_label_list(self):
        eval("label_list").clear()

    # 动态生成云参数配置控件
    def generate_label(self, list):
        count = 1
        for i in list:
            if 'StaticText' in str(i):
                locals()['self.label_' + str(count)] = eval(i)
                eval("label_list").append(locals()['self.label_' + str(count)])
            if 'ComboBox' in str(i):
                locals()['self.combo_box_' + str(count)] = eval(i)
                locals()['self.combo_box_' + str(count)].SetMinSize((110, 30))
                locals()['self.combo_box_' + str(count)].SetSelection(0)
                eval("label_list").append(locals()['self.combo_box_' + str(count)])
            if 'TextCtrl' in str(i):
                locals()['self.text_ctrl_' + str(count)] = eval(i)
                eval("label_list").append(locals()['self.text_ctrl_' + str(count)])
            if 'GridTableBase' in str(i):
                locals()['self.list_ctrl_' + str(count)] = eval(i)
                eval("label_list").append(locals()['self.list_ctrl_' + str(count)])
            count += 1

    def cloud_interface_change(self, event):
        panel = "self.setting_config_page"
        rb = self.cloud_type_combo_box.GetStringSelection()
        self.Destroy_Window()
        self.clear_label_list()
        if rb in ('TCP私有云', 'UDP私有云', 'TCP', 'UDP'):
            socket_list = self.cloud_config.socket_interface(panel, LANGUAGE)
            self.generate_label(socket_list)

        elif rb in ('MQTT私有云', 'MQTT'):
            mqtt_list = self.cloud_config.mqtt_interface(panel, LANGUAGE)
            self.generate_label(mqtt_list)

        elif rb in ('阿里云', '腾讯云', 'aliyun', 'txyun'):
            aliyun_txyun_list = self.cloud_config.aliyun_txyun_interface(panel, LANGUAGE)
            self.generate_label(aliyun_txyun_list)

        elif rb in ('移远云', 'quectel'):
            quecthing_list = self.cloud_config.quecthing_interface(panel, LANGUAGE)
            self.generate_label(quecthing_list)

        elif rb in ('华为云', 'huawei'):
            huweiyun_list = self.cloud_config.huaweiyun_interface(panel, LANGUAGE)
            self.generate_label(huweiyun_list)

    # 串口相关功能函数
    def open_serial(self, event):
        global ser
        if ser.isOpen():
            try:
                self.ser_recv_timer.Stop()
                ser.close()
                pub.sendMessage('uiUpdate', arg1="serialStaChange", arg2=serialList)
            except:
                pass
        else:
            comStr = self.uart_port_list_combo_box.GetString(self.uart_port_list_combo_box.GetCurrentSelection()).split(' ')
            if len(comStr) <= 2:
                wx.MessageBox(u'未检测到串口', u'错误', wx.YES_DEFAULT | wx.ICON_ERROR)
            else:
                ser.port = comStr[1]
                ser.baudrate = int(self.uart_bautrate_combo_box.GetString(self.uart_bautrate_combo_box.GetCurrentSelection()))
                ser.bytesize = int(self.uart_bit_len_combo_box.GetString(self.uart_bit_len_combo_box.GetCurrentSelection()))
                ser.parity = self.uart_parity_combo_box.GetString(self.uart_parity_combo_box.GetCurrentSelection())[0:1]
                ser.stopbits = int(self.uart_stop_big_combo_box.GetString(self.uart_stop_big_combo_box.GetCurrentSelection()))
                print(ser.port, ser.baudrate, ser.bytesize, ser.parity, ser.stopbits)
                try:
                    # open serial port
                    ser.open()
                    self.ser_recv_timer.Start(50)
                    pub.sendMessage('uiUpdate', arg1="serialStaChange", arg2=serialList)
                # fresh mod file list
                except Exception as e:
                    wx.MessageBox(u'串口打开失败' + '\n' + str(e), u'错误', wx.YES_DEFAULT | wx.ICON_ERROR)
                    return None

    def update_serial_port_display(self, arg1, arg2):
        global time_now
        time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        # refresh serial list in main frame section
        global is_open
        is_open = False  # 判断串口是否打开
        if arg1 == "serListUpd":
            tmpSerialList = []
            for port, desc, hwid in sorted(serialList):
                # if "Serial Port" in desc:
                tmpSerialList.append(" " + port + " - " + desc.split(" (")[0])
            # Set serial port list box items
            self.uart_port_list_combo_box.SetItems(tmpSerialList)
            if not len(tmpSerialList):
                self.command_display.write(">>> 未检测到MAIN口\n")
            if self.uart_port_list_combo_box.GetSelection() != 0:
                self.uart_port_list_combo_box.SetSelection(0)
        elif arg1 == "serialStaChange":
            global ser
            if ser.isOpen():
                is_open = True
                self.command_display.Clear()
                self.command_display.AppendText("欢迎使用 DTU Tools {}\n".format(time_now))
                self.enable_uart_button.SetLabel(
                    u"关闭串口" if LANGUAGE == 'chinese' else u"close serial"
                )
            else:
                is_open = False
                self.enable_uart_button.SetLabel(
                    u"打开串口" if LANGUAGE == 'chinese' else u"open serial"
                )

    def __display_data_in_command_frame(self, new_str):
        show_data = "[" + time_now + "]" + "   " + str(new_str)
        self.command_display.write(">>> {}\n".format(show_data))


    def __display_in_uart_data_frame(self, data, write_read_state):
        if write_read_state == "write":
            show_data = "[" + time_now + "]" + "发" + "-->" + str(data)
        else:
            show_data = "[" + time_now + "]" + "收" + "<--" + str(data)
        self.uart_data_display.write("{}\n".format(show_data))

    def ser_rcv_handler(self, event):
        global ser, time_now, deviceList, serial_read_buffer
        # time_now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        time_now = datetime.now().strftime("%H:%M:%S:%f")[:-3]
        if ser.port not in deviceList:
            pub.sendMessage('uiUpdate', arg1="serialStaChange", arg2=serialList)
            return None
        try:
            num = ser.inWaiting()
        except:
            self.open_serial(event)
            pub.sendMessage('uiUpdate', arg1="serialStaChange", arg2=serialList)
            return None

        
        if num > 0:
            data = ser.read(num)
            # 移除原有校验
            if data != b'':
                data_string = data.decode()
                # 在串口数据显示框中显示串口接收到的模组的数据
                self.__display_in_uart_data_frame(data_string, "read")
                if serial_read_buffer:
                    data_string = serial_read_buffer + data_string
                    serial_read_buffer = ""
                data_list = data_string.split(",", 2)
                if len(data_list) != 3 or data_list[0] != "99":
                    return
                data_length = data_list[1]
                data_values = data_list[2]
                print(data_values)
                try:
                    data_length_int = int(data_length)
                except:
                    return
                if len(data_values) < data_length_int:
                    serial_read_buffer = data_string
                    return
                if len(data_values) > data_length_int:
                    serial_read_buffer = ""
                    return
                data_dict = json.loads(data_values)
                status_code = data_dict.get("status")
                if status_code == 1:
                    print("code:", data_dict.get("code"))
                    if str(data_dict.get("code")) in basic_setting_funcode:
                        self.__display_data_in_command_frame("设置成功")
                    else:
                        if data_dict.get("code") == 3:
                            self.__dtu_config = data_dict.get("data")
                            self.import_dtu_config()
                        else:
                            self.__display_data_in_command_frame(data_dict.get("data"))
                else:
                    self.__display_data_in_command_frame(data_dict.get("error"))
        
    def __fill_aliyun_config(self, cloud_config):
        label_list_get = eval("label_list")
        if cloud_config["burning_method"] == 1:
            label_list_get[1].SetSelection(1)
        elif cloud_config["burning_method"] == 0:
            label_list_get[1].SetSelection(0)
        label_list_get[4].write(str(cloud_config["keep_alive"]))
        if cloud_config["client_id"] != "":
            label_list_get[7].write(cloud_config["client_id"])
        if cloud_config["DK"] != "":
            label_list_get[10].write(cloud_config["DK"])
        if cloud_config["PK"] != "":
            label_list_get[13].write(cloud_config["PK"])
        if cloud_config["DS"] != "":
            label_list_get[16].write(cloud_config["DS"])
        if cloud_config["PS"] != "":
            label_list_get[19].write(cloud_config["PS"])
        if cloud_config["clean_session"] == 1:
            label_list_get[22].SetSelection(1)
        elif cloud_config["clean_session"] == 0:
            label_list_get[22].SetSelection(0)
        if cloud_config["qos"] == 1:
            label_list_get[25].SetSelection(1)
        elif cloud_config["qos"] == 0:
            label_list_get[25].SetSelection(0)
        label_list_get[28].write(json.dumps(cloud_config["subscribe"]))
        label_list_get[31].write(json.dumps(cloud_config["publish"]))

    def __fill_mqtt_config(self, cloud_config):
        label_list_get = eval("label_list")
        if cloud_config["server"] != "":
            label_list_get[1].write(cloud_config["server"])
        if cloud_config["port"] != "":
            label_list_get[4].write(cloud_config["port"])
        if cloud_config["client_id"] != "":
            label_list_get[7].write(cloud_config["client_id"])
        if cloud_config["username"] != "":
            label_list_get[10].write(cloud_config["username"])
        if cloud_config["password"] != "":
            label_list_get[13].write(cloud_config["password"])
        label_list_get[16].write(str(cloud_config["keep_alive"]))
        if cloud_config["clean_session"] == 1:
            label_list_get[19].SetSelection(1)
        elif cloud_config["clean_session"] == 0:
            label_list_get[19].SetSelection(0)
        if cloud_config["qos"] == 1:
            label_list_get[22].SetSelection(1)
        elif cloud_config["qos"] == 0:
            label_list_get[22].SetSelection(0)

        label_list_get[25].write(json.dumps(cloud_config["subscribe"]))
        label_list_get[28].write(json.dumps(cloud_config["publish"]))

    def __fill_huawei_config(self, cloud_config):
        label_list_get = eval("label_list")
        if cloud_config["DK"] != "":
            label_list_get[1].write(cloud_config["DK"])
        if cloud_config["DS"] != "":
            label_list_get[4].write(cloud_config["DS"])
        label_list_get[7].write(str(cloud_config["keep_alive"]))
        if cloud_config["clean_session"] == 1:
            label_list_get[10].SetSelection(1)
        elif cloud_config["clean_session"] == 0:
            label_list_get[10].SetSelection(0)
        if cloud_config["qos"] == 1:
            label_list_get[13].SetSelection(1)
        elif cloud_config["qos"] == 0:
            label_list_get[13].SetSelection(0)
        label_list_get[16].write(json.dumps(cloud_config["subscribe"]))
        label_list_get[19].write(json.dumps(cloud_config["publish"]))

    def __fill_quecthing_config(self, cloud_config):
        label_list_get = eval("label_list")
        
        if cloud_config["DK"] != "":
            label_list_get[1].write(cloud_config["DK"])
        if cloud_config["PK"] != "":
            label_list_get[4].write(cloud_config["PK"])
        if cloud_config["DS"] != "":
            label_list_get[7].write(cloud_config["DS"])
        if cloud_config["PS"] != "":
            label_list_get[10].write(cloud_config["PS"])
        label_list_get[13].write(str(cloud_config["keep_alive"]))
        if cloud_config["clean_session"] == 1:
            label_list_get[16].SetSelection(1)
        elif cloud_config["clean_session"] == 0:
            label_list_get[16].SetSelection(0)
        if cloud_config["qos"] == 1:
            label_list_get[19].SetSelection(1)
        elif cloud_config["qos"] == 0:
            label_list_get[19].SetSelection(0)
    
    def __fill_socket_config(self, cloud_config):
        label_list_get = eval("label_list")
        if cloud_config["ip_type"] == "IPv4":
            label_list_get[1].SetSelection(0)
        elif cloud_config["ip_type"] == "IPv6":
            label_list_get[1].SetSelection(1)

        if cloud_config["server"] != "":
            label_list_get[3].write(cloud_config["server"])
        if cloud_config["port"] != "":
            label_list_get[6].write(cloud_config["port"])
        if cloud_config["keep_alive"] != "":
            label_list_get[9].write(str(cloud_config["keep_alive"]))  

    def import_dtu_config(self):
        # set dtu congfig to gui pannel
        print("cloud name:", self.__dtu_config["system_config"]["cloud"])
        if self.__dtu_config["system_config"]["cloud"] == "aliyun":
            self.cloud_type_combo_box.SetSelection(0)
            # 更新云配置界面
            self.cloud_interface_change(0)
            self.__fill_aliyun_config(self.__dtu_config["aliyun_config"])
        elif self.__dtu_config["system_config"]["cloud"] == "txyun":
            self.cloud_type_combo_box.SetSelection(1)
            # 更新云配置界面
            self.cloud_interface_change(0)
            self.__fill_aliyun_config(self.__dtu_config["txyun_config"])
        elif self.__dtu_config["system_config"]["cloud"] == "hwyun":
            self.cloud_type_combo_box.SetSelection(2)
            # 更新云配置界面
            self.cloud_interface_change(0)
            self.__fill_huawei_config(self.__dtu_config["hwyun_config"])
        elif self.__dtu_config["system_config"]["cloud"] == "quecthing":
            self.cloud_type_combo_box.SetSelection(3)
            # 更新云配置界面
            self.cloud_interface_change(0)
            self.__fill_quecthing_config(self.__dtu_config["quecthing_config"])
        elif self.__dtu_config["system_config"]["cloud"] == "tcp_private_cloud":
            self.cloud_type_combo_box.SetSelection(4)
            # 更新云配置界面
            self.cloud_interface_change(0)
            self.__fill_socket_config(self.__dtu_config["tcp_private_cloud_config"])
        elif self.__dtu_config["system_config"]["cloud"] == "mqtt_private_cloud":
            self.cloud_type_combo_box.SetSelection(5)
            # 更新云配置界面
            self.cloud_interface_change(0)
            self.__fill_mqtt_config(self.__dtu_config["mqtt_private_cloud_config"])
            
        if self.__dtu_config["system_config"]["base_function"]["fota"]:
            self.fota_combo_box.SetSelection(1)
        else:
            self.fota_combo_box.SetSelection(0)

        if self.__dtu_config["system_config"]["base_function"]["sota"]:
            self.sota_combo_box.SetSelection(1)
        else:
            self.sota_combo_box.SetSelection(0)

        if self.__dtu_config["system_config"]["base_function"]["offline_storage"]:
            self.offline_storage_combo_box.SetSelection(1)
        else:
            self.offline_storage_combo_box.SetSelection(0)

        if self.__dtu_config["uart_config"]["port"] == "0":
            self.uart_port_num_combo_box.SetSelection(0)
        elif self.__dtu_config["uart_config"]["port"] == "1":
            self.uart_port_num_combo_box.SetSelection(1)
        elif self.__dtu_config["uart_config"]["port"] == "2":
            self.uart_port_num_combo_box.SetSelection(2)

        if self.__dtu_config["uart_config"]["baudrate"] == "1200":
            self.uart_baudrate_combo_box.SetSelection(0)
        elif self.__dtu_config["uart_config"]["baudrate"] == "2400":
            self.uart_baudrate_combo_box.SetSelection(1)
        elif self.__dtu_config["uart_config"]["baudrate"] == "4800":
            self.uart_baudrate_combo_box.SetSelection(2)
        elif self.__dtu_config["uart_config"]["baudrate"] == "9600":
            self.uart_baudrate_combo_box.SetSelection(3)
        elif self.__dtu_config["uart_config"]["baudrate"] == "14400":
            self.uart_baudrate_combo_box.SetSelection(4)
        elif self.__dtu_config["uart_config"]["baudrate"] == "19200":
            self.uart_baudrate_combo_box.SetSelection(5)
        elif self.__dtu_config["uart_config"]["baudrate"] == "28800":
            self.uart_baudrate_combo_box.SetSelection(6)
        elif self.__dtu_config["uart_config"]["baudrate"] == "38400":
            self.uart_baudrate_combo_box.SetSelection(7)
        elif self.__dtu_config["uart_config"]["baudrate"] == "57600":
            self.uart_baudrate_combo_box.SetSelection(8)
        elif self.__dtu_config["uart_config"]["baudrate"] == "115200":
            self.uart_baudrate_combo_box.SetSelection(9)
        elif self.__dtu_config["uart_config"]["baudrate"] == "230400":
            self.uart_baudrate_combo_box.SetSelection(10)
        elif self.__dtu_config["uart_config"]["baudrate"] == "460800":
            self.uart_baudrate_combo_box.SetSelection(11)
        elif self.__dtu_config["uart_config"]["baudrate"] == "921600":
            self.uart_baudrate_combo_box.SetSelection(11)
        
        if self.__dtu_config["uart_config"]["parity"] == "0":
            self.uart_parity_combo_box.SetSelection(0)
        elif self.__dtu_config["uart_config"]["parity"] == "1":
            self.uart_parity_combo_box.SetSelection(1)
        elif self.__dtu_config["uart_config"]["parity"] == "2":
            self.uart_parity_combo_box.SetSelection(2)

        if self.__dtu_config["uart_config"]["databits"] == "8":
            self.uart_databits_combo_box.SetSelection(1)
        elif self.__dtu_config["uart_config"]["databits"] == "7":
            self.uart_databits_combo_box.SetSelection(0)

        if self.__dtu_config["uart_config"]["stopbits"] == "1":
            self.uart_stopbits_combo_box.SetSelection(0)
        elif self.__dtu_config["uart_config"]["stopbits"] == "2":
            self.uart_stopbits_combo_box.SetSelection(1)

        if self.__dtu_config["uart_config"]["flowctl"] == "0":
            self.uart_flowctl_combo_box.SetSelection(0)
        elif self.__dtu_config["uart_config"]["flowctl"] == "1":
            self.uart_flowctl_combo_box.SetSelection(1)

        if self.__dtu_config["uart_config"]["rs485_direction_pin"] != "":
            self.rs485_direction_pin_txt_ctrl.write(self.__dtu_config["uart_config"]["rs485_direction_pin"])

        self.filter_txt_ctrl.Clear()
        self.filter_txt_ctrl.write(self.__dtu_config["usr_config"]["filter_mask"])

    def __request_dtu_config(self):
        print("发送请求DTU配置参数")
        # get dtu config
        data = {"cmd_code": 3, "data": {}}
        send_datas = self.__package_data(data)
        self.__display_in_uart_data_frame(send_datas, "write") # 在串口数据显示框中显示发送数据
        ser.write(send_datas.encode("utf-8"))

    def open_setting_config(self, event):
        if not ser.isOpen():
            wx.MessageBox(u'请先打开USB Serial Port 串口', u'提示', wx.YES_DEFAULT | wx.ICON_INFORMATION)
            return None
        self.main_page.SetSelection(1)
        # set cloud default setting
        self.cloud_type_combo_box.SetSelection(0)
        self.cloud_interface_change(0)
        self.__request_dtu_config()

    # 清空发送框
    def clear_data(self, event):
        if event.GetId() == 1000:
            self.uart_data_display.Clear()
        if event.GetId() == 1001:
            self.uart_send_display.Clear()
        if event.GetId() == 1002:
            self.command_display.Clear()

    def __package_data(self, datas):
        if isinstance(datas, str):
            str_datas = datas
        else:
            str_datas = json.dumps(datas)
        # 减少报文长度,加入99开头的GUI识别码
        data_format = "99,{},{}".format(len(str_datas), str_datas)
        return data_format

    # 发送串口数据
    def send_data(self, event):
        # 先判断串口是否打开
        if not ser.isOpen():
            wx.MessageBox(u'请先打开USB Serial Port 串口', u'提示', wx.YES_DEFAULT | wx.ICON_INFORMATION)
            return None
        if len(self.uart_send_display.GetValue().replace(' ', '')) == 0:
            self.command_display.write(">>> 请输入指令!\n")
            return
        send_datas = self.uart_send_display.GetValue()
        #send_datas = self.__package_data(input_vals)
        self.__display_in_uart_data_frame(send_datas, "write") # 在串口数据显示框中显示发送数据
        ser.write(send_datas.encode("utf-8"))
        self.command_display.write(">>> 发送成功\n")

    def query_command_handle(self, event):
        global ser
        if not ser.isOpen():
            wx.MessageBox(u'请先打开USB Serial Port 串口', u'提示', wx.YES_DEFAULT | wx.ICON_INFORMATION)
            return None
        if event.GetId() == 2003:
            func_code = 0   # 查询IMEI
        if event.GetId() == 2004:
            func_code = 1 # 查询本机号码
        if event.GetId() == 2005:
            func_code = 2 # 查询信号强度
        if event.GetId() == 2006:
            func_code = 255 # 设备重启
        
        data = {"cmd_code": func_code, 'data': {}}
        send_datas = self.__package_data(data)
        self.__display_in_uart_data_frame(send_datas, "write") # 在串口数据显示框中显示发送数据
        ser.write(send_datas.encode("utf-8"))
    
    def retore_factory_setting(self, event):
        self.__send_config(55, "")

    def dtu_restart(self, event):
        self.__send_config(255, "")

    def __cloud_congif_convert(self, cloud_str):
        if cloud_str == u"阿里云":
            return "aliyun"
        elif cloud_str == u"腾讯云":
            return "txyun"
        elif cloud_str == u"华为云":
            return "hwyun"
        elif cloud_str == u"移远云":
            return "quecthing"
        elif cloud_str == u"TCP私有云":
            return "tcp_private_cloud"
        elif cloud_str == u"MQTT私有云":
            return "mqtt_private_cloud"
    
    def __uart_parity_convert(self, parity):
        if parity == "NONE":
            return "0"
        elif parity == "ODD":
            return "1"
        elif parity == "EVENT":
            return "2"

    def __uart_flowctl_convert(self, parity):
        if parity == "FC_NONE":
            return "0"
        elif parity == "FC_HW":
            return "1"

    def __get_aliyun_config(self):
        label_list_get = eval("label_list")
        print("client_id:", label_list_get[7].GetValue())
        print("client_id type:", type(label_list_get[7].GetValue()))
        aliyun_config = {
            "server": "gzsi5zT5fH3.iot-as-mqtt.cn-shanghai.aliyuncs.com",
            "DK": label_list_get[10].GetValue(),
            "PK": label_list_get[13].GetValue(),
            "DS": label_list_get[16].GetValue(),
            "PS": label_list_get[19].GetValue(),
            "burning_method": int(label_list_get[1].GetStringSelection()),
            "keep_alive": int(label_list_get[4].GetValue()),
            "clean_session": True if label_list_get[22].GetSelection()==1 else False,
            "qos": int(label_list_get[25].GetStringSelection()),
            "client_id":label_list_get[7].GetValue(),
            "subscribe": json.loads(label_list_get[28].GetValue()),
            "publish": json.loads(label_list_get[31].GetValue()),
        }
        print("aliyun_config:", aliyun_config)
        return aliyun_config

    def __get_mqtt_config(self):
        label_list_get = eval("label_list")
        mqtt_config = {
            "server": label_list_get[1].GetValue(),
            "port": label_list_get[4].GetValue(),
            "client_id": label_list_get[7].GetValue(),
            "username": label_list_get[10].GetValue(),
            "password": label_list_get[13].GetValue(),
            "clean_session": True if label_list_get[19].GetSelection() == 1 else False,
            "qos": int(label_list_get[22].GetStringSelection()),
            "keep_alive": int(label_list_get[16].GetValue()),
            "subscribe": json.loads(label_list_get[25].GetValue()),
            "publish": json.loads(label_list_get[28].GetValue()),
        }
        print("mqtt_config:", mqtt_config)
        return mqtt_config

    def __get_huawei_config(self):
        label_list_get = eval("label_list")
        huaweiyun_config = {
            "server": "a15fbbd7ce.iot-mqtts.cn-north-4.myhuaweicloud.com",
            "port": "1883",
            "DK": label_list_get[1].GetValue(),
            "PK": "",
            "DS": label_list_get[4].GetValue(),
            "PS": "",
            "keep_alive": int(label_list_get[7].GetValue()),
            "clean_session": True if label_list_get[10].GetSelection()==1 else False,
            "qos": int(label_list_get[13].GetStringSelection()),
            "subscribe": json.loads(label_list_get[16].GetValue()),
            "publish": json.loads(label_list_get[19].GetValue()),
        }
        print("huaweiyun_config:", huaweiyun_config)
        return huaweiyun_config

    def __get_quecthing_config(self):
        label_list_get = eval("label_list")
        quecthing_config = {
            "server":"iot-south.quectel.com",
            "port": "1883",
            "DK": label_list_get[1].GetValue(),
            "PK": label_list_get[4].GetValue(),
            "DS": label_list_get[7].GetValue(),
            "PS": label_list_get[10].GetValue(),
            "keep_alive": int(label_list_get[13].GetValue()),
            "clean_session": True if label_list_get[16].GetSelection()==1 else False,
            "qos": int(label_list_get[19].GetStringSelection()),
        }
        print("quecthing_config:", quecthing_config)
        return quecthing_config

    def __get_socket_config(self):
        label_list_get = eval("label_list")
        socket_config = {
            "ip_type": label_list_get[1].GetValue(),
            "server": label_list_get[3].GetValue(),
            "port": label_list_get[6].GetValue(),
            "keep_alive": int(label_list_get[9].GetValue()),
        }
        print("socket_config:", socket_config)
        return socket_config

    def __send_config(self, func_code, data):
        if func_code == 50:
            data = {"data": {"fota": data}, "cmd_code": func_code}
        elif func_code == 51:
            data = {"data": {"sota": data}, "cmd_code": func_code}
        elif func_code == 52:
            data = {"data": {"offline_storage": data}, "cmd_code": func_code}
        elif func_code == 53:
            data = {"data": {"uart_config": data}, "cmd_code": func_code}
        elif func_code == 54:
            data = {"data": {"cloud_type": data[0], "cloud_conf": data[1]}, "cmd_code": func_code}
        elif func_code == 56:
            data = {"data": {"filter_mask": data}, "cmd_code": func_code}
        elif func_code == 55 or func_code == 255:
            data = {"cmd_code": func_code, 'data': {}}
        format_datas = self.__package_data(data)
        self.__display_in_uart_data_frame(format_datas, "write") # 在串口数据显示框中显示发送数据
        ser.write(format_datas.encode("utf-8"))

    def save_config_param(self, event):
        """send modify config parameter to DTU
        """
        print("导入配置参数")
        if not ser.isOpen():
            wx.MessageBox(u'请先打开USB Serial Port 串口', u'提示', wx.YES_DEFAULT | wx.ICON_INFORMATION)
            return None
        dlg = wx.MessageDialog(None, u"是否确认导入配置参数", u"提示", wx.YES_NO | wx.ICON_QUESTION)
        if dlg.ShowModal() == wx.ID_YES:
            # 基本参数
            cloud_type = self.__cloud_congif_convert(self.cloud_type_combo_box.GetStringSelection())
            sota = True if self.sota_combo_box.GetSelection() == 1 else False
            fota = True if self.fota_combo_box.GetSelection() == 1 else False
            history_storage = True if self.offline_storage_combo_box.GetSelection() == 1 else False
            uart_config = {
                "port" : self.uart_port_num_combo_box.GetStringSelection(),
                "baudrate": self.uart_baudrate_combo_box.GetStringSelection(),
                "databits": self.uart_databits_combo_box.GetStringSelection(),
                "parity": self.__uart_parity_convert(self.uart_parity_combo_box.GetStringSelection()),
                "stopbits": self.uart_stopbits_combo_box.GetStringSelection(),
                "flowctl": self.__uart_flowctl_convert(self.uart_flowctl_combo_box.GetStringSelection()),
                "rs485_direction_pin": self.rs485_direction_pin_txt_ctrl.GetStringSelection(),
            }
            if cloud_type == "aliyun" or cloud_type == "txyun":
                cloud_config = self.__get_aliyun_config()
            elif cloud_type == "hwyun":
                cloud_config = self.__get_huawei_config()
            elif cloud_type == "quecthing":
                cloud_config = self.__get_quecthing_config()
            elif cloud_type == "tcp_private_cloud":
                cloud_config = self.__get_socket_config()
            elif cloud_type == "mqtt_private_cloud":
                cloud_config = self.__get_mqtt_config()

            filter_mask = self.filter_txt_ctrl.GetValue(),
            print("filter_mask:", filter_mask)
            
            self.command_display.write(">>> 正在导入配置参数请勿其他操作....\n")
            try:
                self.__send_config(50, fota)
                time.sleep(0.5)
                self.__send_config(51, sota)
                time.sleep(0.5)
                self.__send_config(52, history_storage)
                time.sleep(0.5)
                self.__send_config(53, uart_config)
                time.sleep(0.5)
                self.__send_config(54, (cloud_type, cloud_config))
                time.sleep(0.5)
                self.__send_config(56, filter_mask[0])
                time.sleep(0.5)
                self.command_display.write(">>> 导入配置文件完成\n")
                self.__send_config(255, 0)
                self.command_display.write(">>> 重启DTU...\n")
            except Exception as e:
                self.command_display.write(">>> 导入文件失败\n")
        dlg.Destroy()


# detect serialport
class serialDet(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global serialList, deviceList
        while True:
            deviceList = [i.device for i in serPort.comports()]
            if serialList == [] or serialList != serPort.comports():
                if serialStatus == False:
                    serialList = serPort.comports()
                    pub.sendMessage('uiUpdate', arg1="serListUpd", arg2=serialList)
            time.sleep(1)


class MyApp(wx.App):
    def OnInit(self):
        self.frame = dtu_gui_frame(None, wx.ID_ANY, "")
        self.SetTopWindow(self.frame)
        self.frame.Show()
        # thread: serialDet
        global tSerialDet
        tSerialDet = serialDet()
        tSerialDet.setDaemon(True)  # set as deamon, stop thread while main frame exit
        tSerialDet.start()
        return True


if __name__ == "__main__":
    app = MyApp(0)
    app.MainLoop()
