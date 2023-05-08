vertical_start_pos = "245"


class CloudConfig(object):

    # 华为云 界面模板
    def huaweiyun_interface(self, panel):
        huaweiyun_list = [  
                            'wx.StaticText({}, wx.ID_ANY, u"DK", pos=(20, {}+00))'.format(panel, vertical_start_pos),
                            'wx.TextCtrl({}, 805, "", pos=(170, {}+00))'.format(panel, vertical_start_pos),
                            'wx.StaticText({}, wx.ID_ANY, u"提示：设备名称", pos=(290, {}+00))'.format(panel, vertical_start_pos),

                            'wx.StaticText({}, wx.ID_ANY, u"DS", pos=(20, {}+30))'.format(panel, vertical_start_pos),
                            'wx.TextCtrl({}, 806, "", pos=(170, {}+30))'.format(panel, vertical_start_pos),
                            'wx.StaticText({}, wx.ID_ANY, u"提示：设备密钥", pos=(290, {}+30))'.format(panel, vertical_start_pos),
                           
                            'wx.StaticText({}, wx.ID_ANY, "keep_alive", pos=(20, {}+60))'.format(panel, vertical_start_pos),
                            'wx.TextCtrl({}, 807, "", pos=(170, {}+60))'.format(panel, vertical_start_pos),
                            'wx.StaticText({}, wx.ID_ANY, u"提示：客户端的请求超时时间，默认300s，可选", pos=(290, {}+60))'.format(panel, vertical_start_pos),

                            'wx.StaticText({}, wx.ID_ANY, u"clean_session", pos=(20, {}+90))'.format(panel, vertical_start_pos),
                            'wx.ComboBox({}, wx.ID_ANY, pos=(170, {}+90), choices=["0", "1"],style=wx.CB_READONLY)'.format(panel, vertical_start_pos),
                            'wx.StaticText({}, wx.ID_ANY, u"提示：MQTT是否保存会话标志，默认0，可选", pos=(290, {}+90))'.format(panel, vertical_start_pos),

                            'wx.StaticText({}, wx.ID_ANY, u"QOS", pos=(20, {}+120))'.format(panel, vertical_start_pos),
                            'wx.ComboBox({}, wx.ID_ANY, pos=(170, {}+120), choices=["0", "1"],style=wx.CB_READONLY)'.format(panel, vertical_start_pos),
                            'wx.StaticText({}, wx.ID_ANY, u"提示：MQTT的QOS级别，默认0，可选", pos=(290, {}+120))'.format(panel, vertical_start_pos),

                            'wx.StaticText({}, wx.ID_ANY, u"订阅主题", pos=(20, {}+150))'.format(panel, vertical_start_pos),
                            'wx.TextCtrl({}, 808, "", pos=(170, {}+150))'.format(panel, vertical_start_pos),
                            'wx.StaticText({}, wx.ID_ANY, u"提示：多主题请使用逗号分割", pos=(290, {}+150))'.format(panel, vertical_start_pos),

                            'wx.StaticText({}, wx.ID_ANY, u"发布主题", pos=(20, {}+180))'.format(panel, vertical_start_pos),
                            'wx.TextCtrl({}, 809, "", pos=(170, {}+180))'.format(panel, vertical_start_pos),
                            'wx.StaticText({}, wx.ID_ANY, u"提示：多主题请使用逗号分割", pos=(290, {}+180))'.format(panel, vertical_start_pos)]

                            
        return huaweiyun_list

    def quecthing_interface(self, panel):
        quecthing_list = [
            'wx.StaticText({}, wx.ID_ANY, u"DK", pos=(20, {}+0))'.format(panel, vertical_start_pos),
            'wx.TextCtrl({}, 805, "", pos=(170, {}+0))'.format(panel, vertical_start_pos),
            'wx.StaticText({}, wx.ID_ANY, u"提示：设备名称", pos=(290, {}+0))'.format(panel, vertical_start_pos),

            'wx.StaticText({}, wx.ID_ANY, u"PK", pos=(20, {}+30))'.format(panel, vertical_start_pos),
            'wx.TextCtrl({}, 806, "", pos=(170, {}+30))'.format(panel, vertical_start_pos),
            'wx.StaticText({}, wx.ID_ANY, u"提示：产品Product Key", pos=(290, {}+30))'.format(panel, vertical_start_pos),

            'wx.StaticText({}, wx.ID_ANY, u"DS", pos=(20, {}+60))'.format(panel, vertical_start_pos),
            'wx.TextCtrl({}, 807, "", pos=(170, {}+60))'.format(panel, vertical_start_pos),
            'wx.StaticText({}, wx.ID_ANY, u"提示：设备密钥", pos=(290, {}+60))'.format(panel, vertical_start_pos),

            'wx.StaticText({}, wx.ID_ANY, u"PS", pos=(20, {}+90))'.format(panel, vertical_start_pos),
            'wx.TextCtrl({}, 808, "", pos=(170, {}+90))'.format(panel, vertical_start_pos),
            'wx.StaticText({}, wx.ID_ANY, u"提示：产品密钥", pos=(290, {}+90))'.format(panel, vertical_start_pos),

            'wx.StaticText({}, wx.ID_ANY, "keep_alive", pos=(20, {}+120))'.format(panel, vertical_start_pos),
            'wx.TextCtrl({}, 809, "", pos=(170, {}+120))'.format(panel, vertical_start_pos),
            'wx.StaticText({}, wx.ID_ANY, u"提示：客户端的请求超时时间，默认120s，可选", pos=(290, {}+120))'.format(panel, vertical_start_pos),
            
            'wx.StaticText({}, wx.ID_ANY, u"clean_session", pos=(20, {}+150))'.format(panel, vertical_start_pos),
            'wx.ComboBox({}, wx.ID_ANY, pos=(170, {}+150), choices=[u"关闭", u"开启"],style=wx.CB_READONLY)'.format(panel, vertical_start_pos),
            'wx.StaticText({}, wx.ID_ANY, u"提示：Session加密是否启用，默认关闭，可选", pos=(290, {}+150))'.format(panel, vertical_start_pos),

            'wx.StaticText({}, wx.ID_ANY, u"QOS", pos=(20, {}+180))'.format(panel, vertical_start_pos),
            'wx.ComboBox({}, wx.ID_ANY, pos=(170, {}+180), choices=["0", "1"],style=wx.CB_READONLY)'.format(panel, vertical_start_pos),
            'wx.StaticText({}, wx.ID_ANY, u"提示：QOS级别，默认0，可选", pos=(290, {}+180))'.format(panel, vertical_start_pos),
        ]
        return quecthing_list
    
    # socket 界面模板
    def socket_interface(self, panel):
        socket_list = [
                        'wx.StaticText({}, wx.ID_ANY, "IP类型", pos=(20, {}+0))'.format(panel, vertical_start_pos),
                        'wx.ComboBox({}, wx.ID_ANY, pos=(170, {}+0), choices=["IPv4", "IPv6"],style=wx.CB_READONLY)'.format(panel, vertical_start_pos),
                        
                        'wx.StaticText({}, wx.ID_ANY, "server", pos=(20, {}+30))'.format(panel, vertical_start_pos),
                        'wx.TextCtrl({}, 803, "", pos=(170, {}+30))'.format(panel, vertical_start_pos),
                        'wx.StaticText({}, wx.ID_ANY, u"提示：不包含端口号", pos=(290, {}+30))'.format(panel, vertical_start_pos),

                        'wx.StaticText({}, wx.ID_ANY, "服务器的端口号", pos=(20, {}+60))'.format(panel, vertical_start_pos),
                        'wx.TextCtrl({}, 804, "", pos=(170, {}+60))'.format(panel, vertical_start_pos),
                        'wx.StaticText({}, wx.ID_ANY, u"提示：端口号范围 1~65536", pos=(290, {}+60))'.format(panel, vertical_start_pos),

                        'wx.StaticText({}, wx.ID_ANY, "keep_alive", pos=(20, {}+90))'.format(panel, vertical_start_pos),
                        'wx.TextCtrl({}, 806, "", pos=(170, {}+90))'.format(panel, vertical_start_pos),
                        'wx.StaticText({}, wx.ID_ANY, u"提示：设置TCP保活包间隔时间，value 单位为分钟，范围：1-120", pos=(290, {}+90))'.format(panel, vertical_start_pos)]
        return socket_list

    # aliyun/txyun 界面模板
    def aliyun_txyun_interface(self, panel):
        aliyun_txyun_list = ['wx.StaticText({}, wx.ID_ANY, "burning_method", pos=(20, {}+0))'.format(panel, vertical_start_pos),
                             'wx.ComboBox({}, wx.ID_ANY, pos=(170, {}+0), choices=["0", "1"],style=wx.CB_READONLY)'.format(panel, vertical_start_pos),
                             'wx.StaticText({}, wx.ID_ANY, u"提示：0：一型一密， 1：一机一密", pos=(290, {}+0))'.format(panel, vertical_start_pos),

                             'wx.StaticText({}, wx.ID_ANY, "keep_alive", pos=(20, {}+30))'.format(panel, vertical_start_pos),
                             'wx.TextCtrl({}, 804, "", pos=(170, {}+30))'.format(panel, vertical_start_pos),
                             'wx.StaticText({}, wx.ID_ANY, u"提示：客户端的请求超时时间，默认300s，可选", pos=(290, {}+30))'.format(panel, vertical_start_pos),

                             'wx.StaticText({}, wx.ID_ANY, u"client_id", pos=(20, {}+60))'.format(panel, vertical_start_pos),
                             'wx.TextCtrl({}, 805, "", pos=(170, {}+60))'.format(panel, vertical_start_pos),
                             'wx.StaticText({}, wx.ID_ANY, u"提示：自定义客户端", pos=(290, {}+60))'.format(panel, vertical_start_pos),

                             'wx.StaticText({}, wx.ID_ANY, u"DK", pos=(20, {}+90))'.format(panel, vertical_start_pos),
                             'wx.TextCtrl({}, 806, "", pos=(170, {}+90))'.format(panel, vertical_start_pos),
                             'wx.StaticText({}, wx.ID_ANY, u"提示：设备名称", pos=(290, {}+90))'.format(panel, vertical_start_pos),

                             'wx.StaticText({}, wx.ID_ANY, u"PK", pos=(20, {}+120))'.format(panel, vertical_start_pos),
                             'wx.TextCtrl({}, 807, "", pos=(170, {}+120))'.format(panel, vertical_start_pos),
                             'wx.StaticText({}, wx.ID_ANY, u"提示：产品名称", pos=(290, {}+120))'.format(panel, vertical_start_pos),

                             'wx.StaticText({}, wx.ID_ANY, u"DS", pos=(20, {}+150))'.format(panel, vertical_start_pos),
                             'wx.TextCtrl({}, 808, "", pos=(170, {}+150))'.format(panel, vertical_start_pos),
                             'wx.StaticText({}, wx.ID_ANY, u"提示：设备密钥（使用一型一密认证此参数为空)", pos=(290, {}+150))'.format(panel, vertical_start_pos),

                             'wx.StaticText({}, wx.ID_ANY, u"PS", pos=(20, {}+180))'.format(panel, vertical_start_pos),
                             'wx.TextCtrl({}, 809, "", pos=(170, {}+180))'.format(panel, vertical_start_pos),
                             'wx.StaticText({}, wx.ID_ANY, u"提示：产品密钥（使用一机一密认证时此参数为空)", pos=(290, {}+180))'.format(panel, vertical_start_pos),

                             'wx.StaticText({}, wx.ID_ANY, u"clean_session", pos=(20, {}+210))'.format(panel, vertical_start_pos),
                             'wx.ComboBox({}, wx.ID_ANY, pos=(170, {}+210), choices=["0", "1"],style=wx.CB_READONLY)'.format(panel, vertical_start_pos),
                             'wx.StaticText({}, wx.ID_ANY, u"提示：MQTT是否保存会话标志，默认0，可选", pos=(290, {}+210))'.format(panel, vertical_start_pos),

                             'wx.StaticText({}, wx.ID_ANY, u"QOS", pos=(20, {}+240))'.format(panel, vertical_start_pos),
                             'wx.ComboBox({}, wx.ID_ANY, pos=(170, {}+240), choices=["0", "1"],style=wx.CB_READONLY)'.format(panel, vertical_start_pos),
                             'wx.StaticText({}, wx.ID_ANY, u"提示：MQTT的QOS级别，默认0，可选", pos=(290, {}+240))'.format(panel, vertical_start_pos),

                             'wx.StaticText({}, wx.ID_ANY, u"订阅主题", pos=(20, {}+270))'.format(panel, vertical_start_pos),
                             'wx.TextCtrl({}, 812, "", pos=(170, {}+270))'.format(panel, vertical_start_pos),
                             'wx.StaticText({}, wx.ID_ANY, u"提示：多主题请使用逗号分割", pos=(290, {}+270))'.format(panel, vertical_start_pos),
                             
                             'wx.StaticText({}, wx.ID_ANY, u"发布主题", pos=(20, {}+300))'.format(panel, vertical_start_pos),
                             'wx.TextCtrl({}, 813, "", pos=(170, {}+300))'.format(panel, vertical_start_pos),
                             'wx.StaticText({}, wx.ID_ANY, u"提示：多主题请使用逗号分割", pos=(290, {}+300))'.format(panel, vertical_start_pos)]
        return aliyun_txyun_list
    
    # mqtt 界面模板
    def mqtt_interface(self, panel):
        mqtt_list = [
            'wx.StaticText({}, wx.ID_ANY, "server", pos=(20, {}+0))'.format(panel, vertical_start_pos),
            'wx.TextCtrl({}, 803, "", pos=(170, {}+0))'.format(panel, vertical_start_pos),
            'wx.StaticText({}, wx.ID_ANY, u"提示：不包含端口号", pos=(290, {}+0))'.format(panel, vertical_start_pos),

            'wx.StaticText({}, wx.ID_ANY, "服务器的端口号", pos=(20, {}+30))'.format(panel, vertical_start_pos),
            'wx.TextCtrl({}, 804, "", pos=(170, {}+30))'.format(panel, vertical_start_pos),
            'wx.StaticText({}, wx.ID_ANY, u"提示：端口号范围 1~65536", pos=(290, {}+30))'.format(panel, vertical_start_pos),

            'wx.StaticText({}, wx.ID_ANY, "client_id", pos=(20, {}+60))'.format(panel, vertical_start_pos),
            'wx.TextCtrl({}, 805, "", pos=(170, {}+60))'.format(panel, vertical_start_pos),
            'wx.StaticText({}, wx.ID_ANY, u"提示：自定义客户端", pos=(290, {}+60))'.format(panel, vertical_start_pos),

            'wx.StaticText({}, wx.ID_ANY, "password", pos=(20, {}+90))'.format(panel, vertical_start_pos),
            'wx.TextCtrl({}, 806, "", pos=(170, {}+90))'.format(panel, vertical_start_pos),
            'wx.StaticText({}, wx.ID_ANY, u"提示：在服务器上注册的密码", pos=(290, {}+90))'.format(panel, vertical_start_pos),

            'wx.StaticText({}, wx.ID_ANY, "keep_alive", pos=(20, {}+120))'.format(panel, vertical_start_pos),
            'wx.TextCtrl({}, 807, "", pos=(170, {}+120))'.format(panel, vertical_start_pos),
            'wx.StaticText({}, wx.ID_ANY, u"提示：客户端的请求超时时间，默认300s,可选", pos=(290, {}+120))'.format(panel, vertical_start_pos),

            'wx.StaticText({}, wx.ID_ANY, u"clean_session", pos=(20, {}+150))'.format(panel, vertical_start_pos),
            'wx.ComboBox({}, 808, choices=["0", "1"], style=wx.CB_READONLY, pos=(170, {}+150))'.format(panel, vertical_start_pos),
            'wx.StaticText({}, wx.ID_ANY, u"提示：MQTT是否保存会话标志位，默认为0 可选", pos=(290, {}+150))'.format(panel, vertical_start_pos),

            'wx.StaticText({}, wx.ID_ANY, u"QOS", pos=(20, {}+180))'.format(panel, vertical_start_pos),
            'wx.ComboBox({}, 809, choices=["0", "1", "2"], style=wx.CB_READONLY, pos=(170, {}+180))'.format(panel, vertical_start_pos),
            'wx.StaticText({}, wx.ID_ANY, u"提示：MQTT的QOS级别，默认0，可选", pos=(290, {}+180))'.format(panel, vertical_start_pos),

            'wx.StaticText({}, wx.ID_ANY, u"订阅主题", pos=(20, {}+210))'.format(panel, vertical_start_pos),
            'wx.TextCtrl({}, 810, "", pos=(170, {}+210))'.format(panel, vertical_start_pos),
            'wx.StaticText({}, wx.ID_ANY, u"提示：多主题请使用逗号分割", pos=(290, {}+210))'.format(panel, vertical_start_pos),

            'wx.StaticText({}, wx.ID_ANY, u"发布主题", pos=(20, {}+240))'.format(panel, vertical_start_pos),
            'wx.TextCtrl({}, 811, "", pos=(170, {}+240))'.format(panel, vertical_start_pos),
            'wx.StaticText({}, wx.ID_ANY, u"提示：注意主题的格式", pos=(290, {}+240))'.format(panel, vertical_start_pos),
        ]
        return mqtt_list
