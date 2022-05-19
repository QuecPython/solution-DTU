1.拆解文件
2.华为云的父类从DtuMqttTransfer 改为AbstractDtuMqttTransfer
3.在command文件中包含dtu_handler中的类


待修改：
1.command 中配置修改后配置文件修改，但是python运行的参数没有变更
2.set_dtu_mode未使用，参数配置获取未完成
3.删除service_acquire 、version 参数，现在没有使用
4.增加配置参数后，备份参数，若当前参数错误则使用备份参数
