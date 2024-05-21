# -*- coding: utf-8 -*-
import datetime
import platform
import subprocess

import chardet
import redis
from PyQt5.QtCore import pyqtSignal, QThread
from PyQt5.QtWidgets import QListWidgetItem
from redis.sentinel import Sentinel
from rediscluster import RedisCluster
from sshtunnel import SSHTunnelForwarder

from readConfig import ReadConfig, BASE_DIR


class AdbThead(QThread):
    signal = pyqtSignal(str)

    def __init__(self, **kwargs):
        super(AdbThead, self).__init__()
        self.cmd = kwargs.get('cmd')
        self.mode = kwargs.get('mode')
        self.pid = kwargs.get('pid')
        self.device = kwargs.get('dev')
        self.product = kwargs.get('product')

    def run(self):
        print(self.cmd)
        res = subprocess.Popen(self.cmd, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT)
        res.stdin.close()
        iid = res.pid
        if platform.system() == 'Darwin':
            pid_sh = run_cmd(f'ps -ef | grep "{iid}" | grep -v "grep"')
            pid_text = read_sh(pid_sh)
            for i in pid_text.splitlines():
                if i.split()[2] == str(iid):
                    iid = i.split()[1]
                    break
        if self.mode == 1:
            self.pid[self.device] = iid
        if self.mode == 6 or self.mode == 11:
            self.pid['pid_list'].append(iid)
        self.get_log(res)

    def get_log(self, res):
        for line in iter(res.stdout.readline, b''):
            ret = chardet.detect(line)['encoding']
            result = str(line, encoding=ret).strip()
            self.signal.emit(result)
        res.stdout.close()
        if self.mode == 1:
            del self.pid[self.device]
            self.signal.emit('100')
            self.signal.emit(f"---------->设备 {self.product} 停止捕获日志")
        elif self.mode == 2:
            self.signal.emit("---------->结束安装")
        elif self.mode == 6:
            self.signal.emit(f"---------->设备 {self.product} 录屏结束")
        elif self.mode == 7:
            self.signal.emit("---------->结束推送文件")
        elif self.mode == 8:
            self.signal.emit("---------->结束推送文件夹")
        elif self.mode == 11:
            self.signal.emit(f"---------->设备 {self.product} 投屏结束")
        elif self.mode == 14:
            self.signal.emit("---------->结束清理")
        elif self.mode == 15:
            self.signal.emit("---------->结束卸载")
        elif self.mode == 17:
            self.signal.emit("---------->重启结束")
        elif self.mode == 4:
            self.signal.emit(f"---------->Monkey {self.product} Close")
        elif self.mode == 5:
            self.signal.emit("---------->结束截图")
        self.signal.emit('')


class GetDev(QThread):
    signal = pyqtSignal(str)

    def __init__(self, devices, product_list):
        super(GetDev, self).__init__()
        self.devices = devices
        self.product_list = product_list

    def run(self):
        self.get_devices_list()

    def get_devices_list(self):
        sh = run_cmd('adb devices')
        devices = read_sh(sh)
        result = devices.splitlines()
        for i in range(1, len(result)):
            dev_info = result[i]
            if '\tdevice' in dev_info:
                device = dev_info.split('\t')[0]
                product = self.get_manufacturer(device)
                self.devices[product] = device
                self.product_list.append(product)
        if self.product_list:
            self.signal.emit('00001')
            # self.comboBox.setItemText(0, '请选择设备')
            # self.comboBox.addItems(product_list)
        else:
            self.signal.emit('00002')

            # self.comboBox.setItemText(0, '未检测到设备')
        self.signal.emit('10000')

    def get_manufacturer(self, device):
        sh = run_cmd(f'adb -s {device} shell getprop ro.product.manufacturer')
        sh2 = run_cmd(f'adb -s {device} shell getprop ro.product.model')
        manufacturer = read_sh(sh).replace(' ', '')
        model = read_sh(sh2).replace(' ', '-')
        return f'{manufacturer}_{model}'


class GetPack(QThread):
    signal = pyqtSignal(str)

    def __init__(self, cmd, el):
        super(GetPack, self).__init__()
        self.cmd = cmd
        self.listWidget = el

    def run(self):
        self.get_package_list()

    def get_package_list(self):
        sh = run_cmd(self.cmd)
        packages = read_sh(sh)
        if packages:
            self.signal.emit('2001')
            result = packages.splitlines()
            result.sort()
            for line in result:
                line = line.replace('package:', '')
                item = QListWidgetItem(line)
                self.listWidget.addItem(item)
        else:
            self.signal.emit('2002')
        self.signal.emit('2000')


class GetMsg(QThread):
    signal = pyqtSignal(str)

    def __init__(self, **kwargs):
        super(GetMsg, self).__init__()
        self.phone = kwargs.get('phone')
        self.env = kwargs.get('env')
        self.R = ReadConfig()
        self.ssh_items = self.R.get_iterm("ssh")

    def run(self):
        # self.get_verification_code()
        self.get_ssl_redis_msg()

    def get_verification_code(self):
        red_items = self.R.get_iterm(f"redis-{self.env}")
        if eval(red_items['cluster']):
            try:
                sentinel = Sentinel(eval(red_items['redis_cluster_list']), socket_timeout=0.5)
                slave = sentinel.slave_for(red_items['master'],
                                           socket_timeout=0.5,
                                           password=red_items['password'],
                                           db=red_items['db'])
                ver_code = []
                for i in range(1, 4):
                    ver_key = f"ic.ic.user.vc.{self.phone}.{i}"
                    code = slave.get(ver_key)
                    if code:
                        code_str = str(code, "utf-8")
                        if i == 1:
                            msg = f"env: {self.env}, phone: {self.phone}, Login_code: {code_str}\n"
                        elif i == 2:
                            msg = f"env: {self.env}, phone: {self.phone}, Change_code: {code_str}\n"
                        else:
                            msg = f"env: {self.env}, phone: {self.phone}, Retrieve_code: {code_str}\n"
                        ver_code.append(msg)
                slave.close()
                if ver_code:
                    self.signal.emit(''.join(ver_code))
                else:
                    self.signal.emit(f"env: {self.env} - 检查手机号或重新发送验证码！\n")
            except Exception as e:
                self.signal.emit(f"错误:{str(e)},连接redis 集群失败! \n")
        else:
            try:
                pool = redis.ConnectionPool(host=red_items['host'],
                                            port=red_items['port'],
                                            password=red_items['password'],
                                            db=red_items['db'],
                                            decode_responses=True)  # host是redis主机，需要redis服务端和客户端都起着 redis默认端口是6379
                r = redis.Redis(connection_pool=pool)
                ver_code = []
                for i in range(1, 4):
                    ver_key = f"ic.ic..uservc.{self.phone}.{i}"
                    code = r.get(ver_key)
                    if code:
                        code_str = str(code, "utf-8")
                        if i == 1:
                            msg = f"env: {self.env}, phone: {self.phone}, Login_code: {code_str}\n"
                        elif i == 2:
                            msg = f"env: {self.env}, phone: {self.phone}, Change_code: {code_str}\n"
                        else:
                            msg = f"env: {self.env}, phone: {self.phone}, Retrieve_code: {code_str}\n"
                        ver_code.append(msg)
                r.close()
                if ver_code:
                    self.signal.emit(''.join(ver_code))
                else:
                    self.signal.emit(f"env: {self.env} - 检查手机号或重新发送验证码！\n")
            except Exception as e:
                self.signal.emit(f"错误:{str(e)},连接redis 失败\n")

    def get_cluster_code(self):
        redis_cluster_list, password, master, db = ReadConfig().get_redis(f"redis-{self.env}")
        try:
            sentinel = Sentinel(redis_cluster_list, socket_timeout=0.5)
            slave = sentinel.slave_for('mymaster', socket_timeout=0.5, password='lbQ7$c5No^HLsvhV', db=0)
            ver_key = f"ic.ic.user.vc.13716610001.1"
            code = slave.get(ver_key)
            slave.close()
        except Exception as e:
            raise
            # ssh跳板机访问redis集群

    def get_ssl_redis_msg(self):
        red_items = self.R.get_iterm(f"redis-{self.env}")
        host_list = eval(red_items['host'])
        with SSHTunnelForwarder(
                (self.ssh_items['host'], int(self.ssh_items['port'])),
                ssh_username=self.ssh_items['username'],
                ssh_password=self.ssh_items['password'],
                remote_bind_address=(host_list[0]['host'], host_list[0]['port']),
                local_bind_address=('0.0.0.0', 10022)
        ) as server:
            server.start()  # 开启隧道
            red = RedisCluster(startup_nodes=host_list, decode_responses=True)
            # red = redis.Redis(host='127.0.0.1', port=server.local_bind_port, decode_responses=True)
            msg = "没有查询到！"
            key = f"captcha_{self.phone}"
            cur_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            ttl_time = red.ttl(key)
            if red.exists(key) == 1:
                text = red.get(key)
                msg = f"env: {self.env}, phone: {self.phone}, Login_code: {text}, {cur_time}, {ttl_time}\n"
                server.close()
            self.signal.emit(msg)


def get_adb_pid(device, ev):
    pids = []
    if device:
        command = f'adb -s {device} shell ps | findstr {ev}'
        sh = run_cmd(command)
        content = read_sh(sh)
        if content:
            for i in content.splitlines():
                pids.append(i.split()[1])
    return pids


def run_cmd(cmd):
    sh = subprocess.Popen(cmd,
                          shell=True,
                          stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE)
    sh.stdin.close()
    return sh


def read_sh(sh):
    content = sh.stdout.read()
    sh.stdout.close()
    msg = None
    if content:
        encoding = chardet.detect(content)['encoding']
        msg = str(content, encoding=encoding).strip()
    return msg


if __name__ == '__main__':
    pass
