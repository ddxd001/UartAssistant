## **UartAssistant v1.0 - 多功能跨平台串口调试工具**

**软件简介**  
UartAssistant v1.0是基于Python和PyQt5开发的现代化串口调试工具，为嵌入式开发、硬件调试及物联网设备通信提供高效的串口数据交互解决方案。软件采用跨平台设计，支持Windows/Linux/macOS操作系统，具有直观的GUI界面和丰富的功能模块。

**核心功能**  

1. **多模式数据发送**  
   - **手动发送**：自由编辑文本内容，支持快捷键即时发送  
   - **快捷指令**：预置常用AT指令集，支持自定义快捷命令库  
   - **文件传输**：支持二进制/文本文件直接发送，进度条实时显示传输状态  
2. **智能数据收发**  
   - **双格式支持**：ASCII明文与HEX十六进制双向转换  
   - **自动解析**：接收区自动识别0x前缀HEX数据  
   - **实时显示**：毫秒级时间戳标记，支持暂停/清空接收区  
3. **专业参数配置**  
   - **灵活连接**：动态检测可用串口，支持自定义波特率（1200-256000bps）  
   - **高级设置**：数据位（5-8bit）、停止位（1-2bit）、校验位（None/Even/Odd）全参数可调  
4. **增强型功能**  
   - **数据持久化**：接收内容一键导出为txt格式  
   - **流量统计**：实时显示收发字节计数器  
   - **主题切换**：深色/浅色模式自由切换
5. **智能自动保存**
   - **关闭软件自动保存**：快捷发送内容无需重复编辑
   - **窗口内容自动保存**：支持定时自动存储功能和关闭软件自动保存功能
   

**技术特性**  

- 采用多线程架构，确保UI流畅响应  
- 基于QSerialPort实现底层通信  
- 提供Python API接口用于自动化测试  

**应用场景**  
✅ 嵌入式设备调试  
✅ 工业控制器通信  
✅ 智能硬件开发  
✅ 教学实验数据交互  
✅ 物联网设备监控  

**软件优势**  

- 轻量化：单文件体积<50MB  
- 低功耗：CPU占用率<10%  
- 高兼容：支持USB-TTL/RS232/RS485等多种接口  
- 强扩展：模块化设计便于功能扩展  

**UartAssistant v2.0 改进方向（部分）**

<ul>
	<li> 自动协议解析：自动或手动选择协议如：MAVlink、GNSS等数据协议，自动解算出对应信息
	<li> 自动串口参数识别：根据接收数据自动识别出波特率
    <li> 支持配置启动参数：可配置加入用户编写的代码
    <li> GUI风格可编辑：支持用户选择内置的主题、也支持用户自定义的主题、支持用户自定义GUI
    <li> 提供建议可在本项目所在仓库中issues提供
</ul>



项目仓库：https://gitee.com/DdXd007/usart-assistant.git

下载代码请复制以下命令到终端（git bash）执行

```git
git clone https://gitee.com/DdXd007/usart-assistant.git
```

欢迎**fork**本项目并提供**Pull Requests**

作者：代一铭（23009200849）