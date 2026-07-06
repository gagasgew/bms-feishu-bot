################################################################################
# 自动生成的文件。不要编辑！
# Toolchain: GNU Tools for STM32 (13.3.rel1)
################################################################################

# 将这些工具调用的输入和输出添加到构建变量 
C_SRCS += \
../Drivers/CMSIS/DSP/Source/CommonTables/arm_common_tables.c \
../Drivers/CMSIS/DSP/Source/CommonTables/arm_const_structs.c 

OBJS += \
./Drivers/CMSIS/DSP/Source/CommonTables/arm_common_tables.o \
./Drivers/CMSIS/DSP/Source/CommonTables/arm_const_structs.o 

C_DEPS += \
./Drivers/CMSIS/DSP/Source/CommonTables/arm_common_tables.d \
./Drivers/CMSIS/DSP/Source/CommonTables/arm_const_structs.d 


# 每个子目录必须为构建它所贡献的源提供规则
Drivers/CMSIS/DSP/Source/CommonTables/%.o Drivers/CMSIS/DSP/Source/CommonTables/%.su Drivers/CMSIS/DSP/Source/CommonTables/%.cyclo: ../Drivers/CMSIS/DSP/Source/CommonTables/%.c Drivers/CMSIS/DSP/Source/CommonTables/subdir.mk
	arm-none-eabi-gcc "$<" -mcpu=cortex-m3 -std=gnu11 -g3 -DDEBUG -DUSE_HAL_DRIVER -DSTM32F103xB -c -I../Core/Inc -I../Drivers/STM32F1xx_HAL_Driver/Inc -I../Drivers/STM32F1xx_HAL_Driver/Inc/Legacy -I../Drivers/CMSIS/Device/ST/STM32F1xx/Include -I../Drivers/CMSIS/Include -I../Drivers/CMSIS/DSP/Include -O0 -ffunction-sections -fdata-sections -Wall -fstack-usage -fcyclomatic-complexity -MMD -MP -MF"$(@:%.o=%.d)" -MT"$@" --specs=nano.specs -mfloat-abi=soft -mthumb -o "$@"

clean: clean-Drivers-2f-CMSIS-2f-DSP-2f-Source-2f-CommonTables

clean-Drivers-2f-CMSIS-2f-DSP-2f-Source-2f-CommonTables:
	-$(RM) ./Drivers/CMSIS/DSP/Source/CommonTables/arm_common_tables.cyclo ./Drivers/CMSIS/DSP/Source/CommonTables/arm_common_tables.d ./Drivers/CMSIS/DSP/Source/CommonTables/arm_common_tables.o ./Drivers/CMSIS/DSP/Source/CommonTables/arm_common_tables.su ./Drivers/CMSIS/DSP/Source/CommonTables/arm_const_structs.cyclo ./Drivers/CMSIS/DSP/Source/CommonTables/arm_const_structs.d ./Drivers/CMSIS/DSP/Source/CommonTables/arm_const_structs.o ./Drivers/CMSIS/DSP/Source/CommonTables/arm_const_structs.su

.PHONY: clean-Drivers-2f-CMSIS-2f-DSP-2f-Source-2f-CommonTables

