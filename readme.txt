1.拆解文件
2.华为云的父类从DtuMqttTransfer 改为AbstractDtuMqttTransfer
3.在command文件中包含dtu_handler中的类


待修改：
1.command 中配置修改后配置文件修改，但是python运行的参数没有变更
3.set_dtu_mode未使用，参数配置获取未完成
