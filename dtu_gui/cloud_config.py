vertical_start_pos = "245"


class CloudConfig(object):

    # 华为云 界面模板
    def huaweiyun_interface(self, panel, language):
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

                            'wx.StaticText({}, wx.ID_ANY, u"subscribe", pos=(20, {}+150))'.format(panel, vertical_start_pos),
                            'wx.TextCtrl({}, 808, "", pos=(170, {}+150), size=wx.Size(320, -1))'.format(panel, vertical_start_pos),
                            'wx.StaticText({}, wx.ID_ANY, u"提示：多主题请使用逗号分割", pos=(500, {}+150))'.format(panel, vertical_start_pos),

                            'wx.StaticText({}, wx.ID_ANY, u"publish", pos=(20, {}+180))'.format(panel, vertical_start_pos),
                            'wx.TextCtrl({}, 809, "", pos=(170, {}+180), size=wx.Size(320, -1))'.format(panel, vertical_start_pos),
                            'wx.StaticText({}, wx.ID_ANY, u"提示：多主题请使用逗号分割", pos=(500, {}+180))'.format(panel, vertical_start_pos)]

        if language != 'chinese':
            huaweiyun_list[2] = 'wx.StaticText({}, wx.ID_ANY, u"ps: device name", pos=(290, {}+00))'.format(panel, vertical_start_pos)
            huaweiyun_list[5] = 'wx.StaticText({}, wx.ID_ANY, u"ps: device secret key", pos=(290, {}+30))'.format(panel, vertical_start_pos)
            huaweiyun_list[8] = 'wx.StaticText({}, wx.ID_ANY, u"ps: client request timeout, default 300 seconds.", pos=(290, {}+60))'.format(panel, vertical_start_pos)
            huaweiyun_list[11] = 'wx.StaticText({}, wx.ID_ANY, u"ps: keep MQTT session，default 0.", pos=(290, {}+90))'.format(panel, vertical_start_pos)
            huaweiyun_list[14] = 'wx.StaticText({}, wx.ID_ANY, u"ps: MQTT QOS, default 0", pos=(290, {}+120))'.format(panel, vertical_start_pos)
            huaweiyun_list[17] = 'wx.StaticText({}, wx.ID_ANY, u"ps: use commas to separate multiple topics.", pos=(500, {}+150))'.format(panel, vertical_start_pos)
            huaweiyun_list[20] = 'wx.StaticText({}, wx.ID_ANY, u"ps: use commas to separate multiple topics.", pos=(500, {}+180))'.format(panel, vertical_start_pos)

        return huaweiyun_list

    def quecthing_interface(self, panel, language):
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

        if language != 'chinese':
            quecthing_list[2] = 'wx.StaticText({}, wx.ID_ANY, u"ps: device name", pos=(290, {}+0))'.format(panel, vertical_start_pos)
            quecthing_list[5] = 'wx.StaticText({}, wx.ID_ANY, u"ps: product name", pos=(290, {}+30))'.format(panel, vertical_start_pos)
            quecthing_list[8] = 'wx.StaticText({}, wx.ID_ANY, u"ps: device secret key", pos=(290, {}+60))'.format(panel, vertical_start_pos)
            quecthing_list[11] = 'wx.StaticText({}, wx.ID_ANY, u"ps: product secret key", pos=(290, {}+90))'.format(panel, vertical_start_pos)
            quecthing_list[14] = 'wx.StaticText({}, wx.ID_ANY, u"ps: client request timeout, default 120 seconds", pos=(290, {}+120))'.format(panel, vertical_start_pos)
            quecthing_list[16] = 'wx.ComboBox({}, wx.ID_ANY, pos=(170, {}+150), choices=[u"off", u"on"],style=wx.CB_READONLY)'.format(panel, vertical_start_pos)
            quecthing_list[17] = 'wx.StaticText({}, wx.ID_ANY, u"ps: session encryption,default off", pos=(290, {}+150))'.format(panel, vertical_start_pos)
            quecthing_list[20] = 'wx.StaticText({}, wx.ID_ANY, u"ps: QOS, default 0.", pos=(290, {}+180))'.format(panel, vertical_start_pos)

        return quecthing_list
    
    # socket 界面模板
    def socket_interface(self, panel, language):
        socket_list = [
                        'wx.StaticText({}, wx.ID_ANY, "IP type", pos=(20, {}+0))'.format(panel, vertical_start_pos),
                        'wx.ComboBox({}, wx.ID_ANY, pos=(170, {}+0), choices=["IPv4", "IPv6"],style=wx.CB_READONLY)'.format(panel, vertical_start_pos),
                        
                        'wx.StaticText({}, wx.ID_ANY, "server", pos=(20, {}+30))'.format(panel, vertical_start_pos),
                        'wx.TextCtrl({}, 803, "", pos=(170, {}+30))'.format(panel, vertical_start_pos),
                        'wx.StaticText({}, wx.ID_ANY, u"提示：不包含端口号", pos=(290, {}+30))'.format(panel, vertical_start_pos),

                        'wx.StaticText({}, wx.ID_ANY, "server port", pos=(20, {}+60))'.format(panel, vertical_start_pos),
                        'wx.TextCtrl({}, 804, "", pos=(170, {}+60))'.format(panel, vertical_start_pos),
                        'wx.StaticText({}, wx.ID_ANY, u"提示：端口号范围 1~65536", pos=(290, {}+60))'.format(panel, vertical_start_pos),

                        'wx.StaticText({}, wx.ID_ANY, "keep_alive", pos=(20, {}+90))'.format(panel, vertical_start_pos),
                        'wx.TextCtrl({}, 806, "", pos=(170, {}+90))'.format(panel, vertical_start_pos),
                        'wx.StaticText({}, wx.ID_ANY, u"提示：设置TCP保活包间隔时间，value 单位为分钟，范围：1-120", pos=(290, {}+90))'.format(panel, vertical_start_pos)]

        if language != 'chinese':
            socket_list[4] = 'wx.StaticText({}, wx.ID_ANY, u"ps: port excluded.", pos=(290, {}+30))'.format(panel, vertical_start_pos)
            socket_list[7] = 'wx.StaticText({}, wx.ID_ANY, u"ps: port 1~65536", pos=(290, {}+60))'.format(panel, vertical_start_pos)
            socket_list[10] = 'wx.StaticText({}, wx.ID_ANY, u"ps: TCP keep alive interval time, 1-120 minutes", pos=(290, {}+90))'.format(panel, vertical_start_pos)

        return socket_list

    # aliyun/txyun 界面模板
    def aliyun_txyun_interface(self, panel, language):
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

                             'wx.StaticText({}, wx.ID_ANY, u"subscribe", pos=(20, {}+270))'.format(panel, vertical_start_pos),
                             'wx.TextCtrl({}, 812, "", pos=(170, {}+270), size=wx.Size(320, -1))'.format(panel, vertical_start_pos),
                             'wx.StaticText({}, wx.ID_ANY, u"提示：多主题请使用逗号分割", pos=(500, {}+270))'.format(panel, vertical_start_pos),
                             
                             'wx.StaticText({}, wx.ID_ANY, u"publish", pos=(20, {}+300))'.format(panel, vertical_start_pos),
                             'wx.TextCtrl({}, 813, "", pos=(170, {}+300), size=wx.Size(320, -1))'.format(panel, vertical_start_pos),
                             'wx.StaticText({}, wx.ID_ANY, u"提示：多主题请使用逗号分割", pos=(500, {}+300))'.format(panel, vertical_start_pos)]

        if language != 'chinese':
            aliyun_txyun_list[2] = 'wx.StaticText({}, wx.ID_ANY, u"ps: 0：一型一密， 1：一机一密", pos=(290, {}+0))'.format(panel, vertical_start_pos)
            aliyun_txyun_list[5] = 'wx.StaticText({}, wx.ID_ANY, u"ps: client request timeout default 300 seconds.", pos=(290, {}+30))'.format(panel, vertical_start_pos)
            aliyun_txyun_list[8] = 'wx.StaticText({}, wx.ID_ANY, u"ps: client id", pos=(290, {}+60))'.format(panel, vertical_start_pos)
            aliyun_txyun_list[11] = 'wx.StaticText({}, wx.ID_ANY, u"ps: device name", pos=(290, {}+90))'.format(panel, vertical_start_pos)
            aliyun_txyun_list[14] = 'wx.StaticText({}, wx.ID_ANY, u"ps: product name", pos=(290, {}+120))'.format(panel, vertical_start_pos)
            aliyun_txyun_list[17] = 'wx.StaticText({}, wx.ID_ANY, u"ps: device secret key", pos=(290, {}+150))'.format(panel, vertical_start_pos)
            aliyun_txyun_list[20] = 'wx.StaticText({}, wx.ID_ANY, u"ps: product secret key", pos=(290, {}+180))'.format(panel, vertical_start_pos)
            aliyun_txyun_list[23] = 'wx.StaticText({}, wx.ID_ANY, u"ps: MQTT keep session, default 0", pos=(290, {}+210))'.format(panel, vertical_start_pos)
            aliyun_txyun_list[26] = 'wx.StaticText({}, wx.ID_ANY, u"ps: MQTT QOS, default 0", pos=(290, {}+240))'.format(panel, vertical_start_pos)
            aliyun_txyun_list[29] = 'wx.StaticText({}, wx.ID_ANY, u"ps: use commas to separate multiple topics", pos=(500, {}+270))'.format(panel, vertical_start_pos)
            aliyun_txyun_list[32] = 'wx.StaticText({}, wx.ID_ANY, u"ps: use commas to separate multiple topics", pos=(500, {}+300))'.format(panel, vertical_start_pos)

        return aliyun_txyun_list
    
    # mqtt 界面模板
    def mqtt_interface(self, panel, language):
        mqtt_list = [
            'wx.StaticText({}, wx.ID_ANY, "server", pos=(20, {}+0))'.format(panel, vertical_start_pos),
            'wx.TextCtrl({}, 803, "", pos=(170, {}+0))'.format(panel, vertical_start_pos),
            'wx.StaticText({}, wx.ID_ANY, u"提示：不包含端口号", pos=(290, {}+0))'.format(panel, vertical_start_pos),

            'wx.StaticText({}, wx.ID_ANY, "server port", pos=(20, {}+30))'.format(panel, vertical_start_pos),
            'wx.TextCtrl({}, 804, "", pos=(170, {}+30))'.format(panel, vertical_start_pos),
            'wx.StaticText({}, wx.ID_ANY, u"提示：端口号范围 1~65536", pos=(290, {}+30))'.format(panel,
                                                                                                vertical_start_pos),

            'wx.StaticText({}, wx.ID_ANY, "client_id", pos=(20, {}+60))'.format(panel, vertical_start_pos),
            'wx.TextCtrl({}, 805, "", pos=(170, {}+60))'.format(panel, vertical_start_pos),
            'wx.StaticText({}, wx.ID_ANY, u"提示：自定义客户端", pos=(290, {}+60))'.format(panel, vertical_start_pos),

            'wx.StaticText({}, wx.ID_ANY, "username", pos=(20, {}+90))'.format(panel, vertical_start_pos),
            'wx.TextCtrl({}, 806, "", pos=(170, {}+90))'.format(panel, vertical_start_pos),
            'wx.StaticText({}, wx.ID_ANY, u"提示：在服务器上注册的用户名", pos=(290, {}+90))'.format(panel, vertical_start_pos),

            'wx.StaticText({}, wx.ID_ANY, "password", pos=(20, {}+120))'.format(panel, vertical_start_pos),
            'wx.TextCtrl({}, 807, "", pos=(170, {}+120))'.format(panel, vertical_start_pos),
            'wx.StaticText({}, wx.ID_ANY, u"提示：在服务器上注册的密码", pos=(290, {}+120))'.format(panel, vertical_start_pos),

            'wx.StaticText({}, wx.ID_ANY, "keep_alive", pos=(20, {}+150))'.format(panel, vertical_start_pos),
            'wx.TextCtrl({}, 808, "", pos=(170, {}+150))'.format(panel, vertical_start_pos),
            'wx.StaticText({}, wx.ID_ANY, u"提示：客户端的请求超时时间，默认300s,可选", pos=(290, {}+150))'.format(panel, vertical_start_pos),

            'wx.StaticText({}, wx.ID_ANY, u"clean_session", pos=(20, {}+180))'.format(panel, vertical_start_pos),
            'wx.ComboBox({}, 809, choices=["0", "1"], style=wx.CB_READONLY, pos=(170, {}+180))'.format(panel, vertical_start_pos),
            'wx.StaticText({}, wx.ID_ANY, u"提示：MQTT是否保存会话标志位，默认为0 可选", pos=(290, {}+180))'.format(panel, vertical_start_pos),

            'wx.StaticText({}, wx.ID_ANY, u"QOS", pos=(20, {}+210))'.format(panel, vertical_start_pos),
            'wx.ComboBox({}, 810, choices=["0", "1", "2"], style=wx.CB_READONLY, pos=(170, {}+210))'.format(panel, vertical_start_pos),
            'wx.StaticText({}, wx.ID_ANY, u"提示：MQTT的QOS级别，默认0，可选", pos=(290, {}+210))'.format(panel, vertical_start_pos),

            'wx.StaticText({}, wx.ID_ANY, u"subscribe", pos=(20, {}+240))'.format(panel, vertical_start_pos),
            'wx.TextCtrl({}, 811, "", pos=(170, {}+240), size=wx.Size(320, -1))'.format(panel, vertical_start_pos),
            'wx.StaticText({}, wx.ID_ANY, u"提示：自定义主题id为key，主题字符串为value的json格式", pos=(500, {}+240))'.format(panel, vertical_start_pos),

            'wx.StaticText({}, wx.ID_ANY, u"publish", pos=(20, {}+270))'.format(panel, vertical_start_pos),
            'wx.TextCtrl({}, 811, "", pos=(170, {}+270), size=wx.Size(320, -1))'.format(panel, vertical_start_pos),
            'wx.StaticText({}, wx.ID_ANY, u"提示：自定义主题id为key，主题字符串为value的json格式", pos=(500, {}+270))'.format(panel, vertical_start_pos)
        ]

        if language != 'chinese':
            mqtt_list[2] = 'wx.StaticText({}, wx.ID_ANY, u"ps: port excluded", pos=(290, {}+0))'.format(panel, vertical_start_pos)
            mqtt_list[5] = 'wx.StaticText({}, wx.ID_ANY, u"ps: port 1~65536", pos=(290, {}+30))'.format(panel, vertical_start_pos)
            mqtt_list[8] = 'wx.StaticText({}, wx.ID_ANY, u"ps: client id", pos=(290, {}+60))'.format(panel, vertical_start_pos)
            mqtt_list[11] = 'wx.StaticText({}, wx.ID_ANY, u"ps: username registered", pos=(290, {}+90))'.format(panel, vertical_start_pos)
            mqtt_list[14] = 'wx.StaticText({}, wx.ID_ANY, u"ps: password", pos=(290, {}+120))'.format(panel, vertical_start_pos)
            mqtt_list[17] = 'wx.StaticText({}, wx.ID_ANY, u"ps: client request timeout, default 300 seconds", pos=(290, {}+150))'.format(panel, vertical_start_pos)
            mqtt_list[20] = 'wx.StaticText({}, wx.ID_ANY, u"ps: MQTT session alive, default 0", pos=(290, {}+180))'.format(panel, vertical_start_pos)
            mqtt_list[23] = 'wx.StaticText({}, wx.ID_ANY, u"ps: MQTT QOS, default 0", pos=(290, {}+210))'.format(panel, vertical_start_pos)
            mqtt_list[26] = 'wx.StaticText({}, wx.ID_ANY, u"ps: json string", pos=(500, {}+240))'.format(panel, vertical_start_pos)
            mqtt_list[29] = 'wx.StaticText({}, wx.ID_ANY, u"ps: json string", pos=(500, {}+270))'.format(panel, vertical_start_pos)

        return mqtt_list
