import serial
import time
import pyvisa
import matplotlib.pyplot as plt

# LCRメーターの設定
LCR_IP = "192.168.10.22"
rm = pyvisa.ResourceManager()
lcr = rm.open_resource(f"TCPIP::{LCR_IP}::INSTR")
lcr.timeout = 5000  # タイムアウト設定

# **LCRメーターの測定設定**
lcr.write(":FUNC:IMP CPD")  # 並列キャパシタンス測定モード
lcr.write(":SENS:CAP:RANG:AUTO ON")  # 測定範囲を自動調整
lcr.write(":TRIG:SOUR BUS")  # トリガーモードを BUS に設定
time.sleep(0.5)  # 設定が反映されるのを待つ

# RP100の設定
RP100_COM_PORT = 'COM5'
RP100_BAUDRATE = 115200

# グラフの準備
fig, ax = plt.subplots()
voltages = []
capacitances = []

# LCRメーターの接続確認
try:
    lcr.write("*IDN?")
    print("LCR Meter ID:", lcr.read())  # LCRメーターのIDを確認
except pyvisa.VisaIOError as e:
    print(f"LCRメーターとの接続に失敗しました: {e}")
    exit(1)

# チャンネル1を-20Vに設定
with serial.Serial(RP100_COM_PORT, baudrate=RP100_BAUDRATE, timeout=1) as rp100:
    rp100.write(b'OUTP1 1\n')  # チャンネル1の出力をオン
    rp100.write(b'SOUR1:VOLT -20\n')  # チャンネル1の電圧を-20Vに設定
    time.sleep(0.1)

    # チャンネル2を0Vから50Vに1Vごとに5秒待機
    rp100.write(b'OUTP2 1\n')  # チャンネル2の出力をオン
    for volt in range(0, 51):  # 0Vから50Vまで
        rp100.write(f'SOUR2:VOLT {volt}\n'.encode())  # 電圧を設定
        time.sleep(5)  # 5秒待機

        try:
            # **LCRメーターの測定**
            lcr.write("INIT")  # 測定を実行
            lcr.write("*WAI")  # 測定完了を待つ
            capacitance = lcr.query(":FETCh?")  # `Cp` の測定
            capacitance = float(capacitance.split(",")[0])  # 数値に変換

            # データ保存
            voltages.append(volt)
            capacitances.append(capacitance)

            # グラフ更新
            ax.clear()
            ax.plot(voltages, capacitances, label="Cp (pF)")
            ax.set_xlabel('Voltage (V)')
            ax.set_ylabel('Capacitance (pF)')
            ax.legend()
            plt.draw()
            plt.pause(0.1)
        except pyvisa.VisaIOError as e:
            print(f"キャパシタンス値の読み取りエラー: {e}")

    # **測定結果を出力**
    print("\n測定結果:")
    print("Voltage (V) | Capacitance (pF)")
    print("-----------------------------")
    for v, c in zip(voltages, capacitances):
        print(f"{v:>10} V | {c:>10.3f} pF")

# 最後にグラフを表示
plt.show()
