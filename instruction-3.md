系统运行参数表
| 英文指令 | 中文说明 |
|----------|----------|
| `batt_volt` | 电池包额定初始化电压 / 基准电压 |
| `batt_ah` | 电池包标称总容量 (安时) |
| `batt_cycle` | 电池初始循环次数 (Cycle) |
| `batt_r` | 电池包初始直流内阻参考值 |
| `soc_chg_correct` | 常温充电末端 SOC 校准基准电压 |
| `soc_chg_correct_lt` | 低温充电末端 SOC 校准基准电压 |
| `soc_dsg_correct` | 常温放电末端 SOC 校准基准电压 |
| `soc_dsg_correct_lt` | 低温放电末端 SOC 校准基准电压 |
| `soc_full_correct` | 绝对满充强制 100% SOC 校准电压 |
| `soc_start_curr` | SOC 安时积分启动有效电流阈值 |
| `soc_stop_curr` | SOC 安时积分停止计算电流阈值（静置判定） |
| `soc_store_curr` | 触发 SOC 数据强制落盘（EEPROM）电流阈值 |
| `ah_start_curr` | 循环容量（SOH）累计有效电流阈值 |
| `ah_start_temp` | 循环容量（SOH）累计最低有效温度阈值 |
| `r_start_curr` | 动态内阻更新允许的最小阶跃电流阈值 |
| `heat_start_t` | 自动加热功能启动温度阈值 |
| `heat_stop_t` | 自动加热功能停止温度阈值 |
| `prechg_timeout` | 预充电阶段最大允许超时时间 |
| `sleep_volt` | 允许系统进入深度休眠的最高母线电压阈值 |
| `enter_sleep_dly` | 满足休眠条件后的延迟倒计时（防止频繁唤醒） |
| `beep_func` | 蜂鸣器功能硬件使能开关 (0:关, 1:开) |
| `button_type` | 外部物理按键类型配置 (0:自锁式, 1:自复位式) |
| `logic_id` | 电池包的逻辑/物理通信从站 ID |
| `heating_func` | 自动加热管理模块全局使能开关 (0:关, 1:开) |
