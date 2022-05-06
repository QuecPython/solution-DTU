1.拆解文件
2.华为云的父类从DtuMqttTransfer 改为AbstractDtuMqttTransfer
3.在command文件中包含dtu_handler中的类


待修改：
1.command 中配置修改后配置文件修改，但是python运行的参数没有变更
2.command 中 get_network_connect命名：目前新的阿里云和移远云中还没有check_net()接口
3.set_dtu_mode未使用，参数配置获取未完成
4.历史记录还没有增加
