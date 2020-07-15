#Ver 0.0.1
import ruamel.yaml as yaml
import hashlib, os, time, json, base64, string, random, threading, requests
from Crypto.Cipher import AES as _AES

NowVer = 11
PlayerList = {}
PlayerEvent = []
cfg = {}
Loop = True
LoopLoadsThread = None

def log(server, text, type='info'):
    if type == 'info':
        cmd = server.logger.info
    elif type == 'warning':
        cmd = server.logger.warning
    elif type == 'error':
        cmd = server.logger.error
    else:
        raise TypeError("Parameter 'type' must be info/warning/error !")
    for each in str(text).split('\n'):
        cmd(each)

def SavePSD(text):
    aes = _AES.new(str.encode(cfg['PlayerSystemConfig']['datakey']), 1)
    while len(text) % 16 != 0:
        text += '\0'
    text = str.encode(text)
    encryptedText = base64.encodebytes(aes.encrypt(text))
    open('config/PlayerSystem/PSD', 'w').write(str(encryptedText, encoding='utf-8').replace('\n', ''))

def LoadPSD():
    aes = _AES.new(str.encode(cfg['PlayerSystemConfig']['datakey']), 1)
    text = open('config/PlayerSystem/PSD', 'r').read()
    text = bytes(text, encoding='utf-8')
    decryptedText = aes.decrypt(base64.decodebytes(text)).rstrip(b'\0').decode("utf8")
    return str(decryptedText)

def LoopLoads(server):
    while Loop:
        for each in PlayerEvent:
            if each['Type'] == 'Loop':
                if each['Pass'] != None:
                    if each['Pass']:
                        PlayerEvent.remove(each)
                    else:
                        server.rcon_query(each['Text'])
                else:
                    server.rcon_query(each['Text'])
                    each['Times'] -= 1
                    if each['Times'] == 0:
                        PlayerEvent.remove(each)

def on_load(server, old_module):
    if server.is_server_startup():
        log(server, '正在重新加载PlayerSystem，请稍等...')
        on_server_startup(server)

def on_server_startup(server):
    global PlayerList, cfg, LoopLoadsThread
    log(server, '检测到服务端启动完成，开始初始化...')
    log(server, '正在检查更新...')
    times1 = 0
    while True:
        try:
            res = requests.get('https://gitee.com/LYF511511/MCDRPlugins/raw/master/PlayerSystem/plugins/PlayerSystem.py')
        except Exception:
            res.status_code = 404
        if res.status_code == 200:
            text = res.text
            if int(''.join(text.split('\n')[0][4:].split('.'))) > NowVer:
                log(server, '检测到插件有最新版本，正在开始更新...')
                times2 = 0
                while True:
                    try:
                        res = requests.get('https://gitee.com/LYF511511/MCDRPlugins/raw/master/PlayerSystem/config/PlayerSystem/Config.yml')
                    except Exception:
                        res.status_code = 404
                    if res.status_code == 200:
                        cfgfile = res.text
                        break
                    else:
                        times2 += 1
                        log(server, '尝试获取配置文件失败（%d/5）'%(times2))
                    if times2 == 5:
                        log(server, '获取配置文件失败，请检查网络连接，将写入默认配置文件')
                        cfgfile = '# PlayerSystem 配置文件\n\n# PlayerSystem 配置\nPlayerSystemConfig: {\n    # 白名单配置 注：必须开启登录\n    WhiteList: {\n        enable: false, # 是否启用\n        shownum: 6,    #白名单列表显示玩家个数\n    },\n    # 自动登录配置 注：必须开启登录\n    AutoLogin: {\n        enable: false,  # 是否启用\n        day: 5,         # 自动登录天数（现实世界）\n    },\n    # 登录设置\n    Login: {\n        enable: false, # 是否启用\n        pwdlen: 5,     # 随机密码长度\n        saltlen: 5,    # 随机数长度\n        chance: 3,     # 尝试次数\n        seconds: 60    # 不注册自动踢出秒数\n    },\n    # 文件密码（长度必须为16 24 32）请勿随便更改，否则会丢失数据！\n    datakey: \'0123456789012345\'\n}\n\n# 文字设置 §\nTextConfig: {\n    nowhitelist: \'§8[§6玩家系统§8]§c 你还没有白名单\',\n    welcome: \'§8[§6玩家系统§8]§a 欢迎进入服务器\',\n    autologin: \'§8[§6玩家系统§8]§a 自动登录成功\',\n    login: \'§8[§6玩家系统§8]§c 请使用命令"!!log 密钥"登录，随机数为{salt}\',\n    pwdwrong: \'§8[§6玩家系统§8]§c 密码错误，请重新输入\',\n    pwdreset: \'§8[§6玩家系统§8]§a {name}成功重置密码，新密码为{pwd}\',\n    nopermission: \'§8[§6玩家系统§8]§c 你没有权限\',\n    loginsuccess: \'§8[§6玩家系统§8]§a 登录成功\',\n    registersuccess: \'§8[§6玩家系统§8]§a {name}注册成功，密码为{pwd}，已自动登录\',\n    chanceover: \'§8[§6玩家系统§8]§c 给你的机会已用尽\',\n    timeover: \'§8[§6玩家系统§8]§c 登录超时\',\n    nostate: \'§8[§6玩家系统§8]§c 你没有这个状态\'\n}'
                with open("config/PlayerSystem/Config.yml", 'w', encoding='utf-8') as f:
                    f.write(cfgfile)
                with open('plugins/PlayerSystem.py', 'w', encoding='utf-8') as f:
                    f.write(text)
                log(server, '更新成功，正在重载插件...')
                server.load_plugin('PlayerSystem')
            else:
                log(server, '插件已是最新版')
            break
        else:
            times1 += 1
            log(server, '尝试更新插件失败（%d/5）'%(times1))
        if times1 == 5:
            log(server, '更新插件失败，请检查网络连接')
    log(server, '检查更新完成')
    log(server, '正在加载配置文件...')
    if not os.path.exists('config/PlayerSystem/Config.yml'):
        log(server, '检测到没有配置文件，正在获取...')
        if not os.path.exists('config/PlayerSystem'):
            os.mkdir('config/PlayerSystem')
        times = 0
        while True:
            try:
                res = requests.get('https://gitee.com/LYF511511/MCDRPlugins/raw/master/PlayerSystem/config/PlayerSystem/Config.yml')
            except Exception:
                res.status_code = 404
            if res.status_code == 200:
                cfgfile = res.text
                break
            else:
                times += 1
                log(server, '尝试获取配置文件失败（%d/5）'%(times))
            if times == 5:
                log(server, '获取配置文件失败，请检查网络连接，将写入默认配置文件')
                cfgfile = '# PlayerSystem 配置文件\n\n# PlayerSystem 配置\nPlayerSystemConfig: {\n    # 白名单配置 注：必须开启登录\n    WhiteList: {\n        enable: false, # 是否启用\n        shownum: 6,    #白名单列表显示玩家个数\n    },\n    # 自动登录配置 注：必须开启登录\n    AutoLogin: {\n        enable: false,  # 是否启用\n        day: 5,         # 自动登录天数（现实世界）\n    },\n    # 登录设置\n    Login: {\n        enable: false, # 是否启用\n        pwdlen: 5,     # 随机密码长度\n        saltlen: 5,    # 随机数长度\n        chance: 3,     # 尝试次数\n        seconds: 60    # 不注册自动踢出秒数\n    },\n    # 文件密码（长度必须为16 24 32）请勿随便更改，否则会丢失数据！\n    datakey: \'0123456789012345\'\n}\n\n# 文字设置 §\nTextConfig: {\n    nowhitelist: \'§8[§6玩家系统§8]§c 你还没有白名单\',\n    welcome: \'§8[§6玩家系统§8]§a 欢迎进入服务器\',\n    autologin: \'§8[§6玩家系统§8]§a 自动登录成功\',\n    login: \'§8[§6玩家系统§8]§c 请使用命令"!!log 密钥"登录，随机数为{salt}\',\n    pwdwrong: \'§8[§6玩家系统§8]§c 密码错误，请重新输入\',\n    pwdreset: \'§8[§6玩家系统§8]§a {name}成功重置密码，新密码为{pwd}\',\n    nopermission: \'§8[§6玩家系统§8]§c 你没有权限\',\n    loginsuccess: \'§8[§6玩家系统§8]§a 登录成功\',\n    registersuccess: \'§8[§6玩家系统§8]§a {name}注册成功，密码为{pwd}，已自动登录\',\n    chanceover: \'§8[§6玩家系统§8]§c 给你的机会已用尽\',\n    timeover: \'§8[§6玩家系统§8]§c 登录超时\',\n    nostate: \'§8[§6玩家系统§8]§c 你没有这个状态\'\n}'
        with open("config/PlayerSystem/Config.yml", 'w', encoding='utf-8') as f:
            f.write(cfgfile)
    with open("config/PlayerSystem/Config.yml", 'r', encoding='utf-8') as f:
        cfg = yaml.load(f)
    log(server, '加载配置文件完成')
    log(server, '正在读取玩家列表...')
    if not os.path.exists('config/PlayerSystem/PSD'):
        SavePSD('{}')
    PlayerList = json.loads(LoadPSD())
    log(server, '读取玩家列表完成，共读取到%d个玩家'%(len(PlayerList.items())))
    log(server, '正在加载处理线程...')
    if LoopLoadsThread == None:
        LoopLoadsThread = threading.Thread(target=LoopLoads, name='LoopLoads', args=(server, ))
        LoopLoadsThread.start()
    log(server, '加载处理线程成功')
    log(server, '正在检测 Rcon...')
    if server.is_rcon_running():
        log(server, 'Rcon 已加载')
    else:
        log(server, 'Rcon 未加载，可能导致插件无法使用')
    log(server, 'Rcon 检测成功')

def on_user_info(server, info):
    global PlayerList, PlayerEvent
    text = info.content.split(' ')
    keys = list(PlayerList.keys())
    player = info.player
    if text[0] == '!!ReloadPlayerSystem':
        if server.get_permission_level(info) < 3:
            server.reply(info, cfg['TextConfig']['nopermission'])
            return
        log(server, '正在重新加载PlayerSystem，请稍等...')
        on_server_startup(server)
    if text[0] == '!!WhiteList'or text[0] == '!!WL':
        if server.get_permission_level(info) < 3:
            server.reply(info, cfg['TextConfig']['nopermission'])
            return
        if len(text) == 1:
            if player == None:
                log(server, '白名单管理命令\n!!WL：显示这条消息\n!!WL add 玩家：添加玩家到白名单\n!!WL del 玩家：删除玩家白名单\n!!WL list [页数]：白名单玩家名单')
            else:
                server.tell(player, '白名单管理命令\n!!WL：显示这条消息\n!!WL add 玩家：添加玩家到白名单\n!!WL del 玩家：删除玩家白名单\n!!WL list [页数]：白名单玩家名单'%text[2])
        elif text[1] == 'add':
            if len(text) == 2:
                server.reply(info, '!!WL add 玩家：添加玩家到白名单')
                return
            if PlayerList.get(text[2]) == text[2]:
                server.reply(info, '昵称重复')
                return
            PlayerList[text[2]] = {'Pwd':None, 'LastTime':0}
            SavePSD(json.dumps(PlayerList))
            server.reply(info, '已添加%s到白名单'%(text[2]))
        elif text[1] == 'del':
            if len(text) == 2:
                server.reply(info, '!!WL del 玩家：删除玩家白名单')
                return
            if PlayerList.get(text[2], None) == None:
                server.reply(info, '未在白名单找到%s'%(text[2]))
                return
            else:
                PlayerList.pop(text[2])
                SavePSD(json.dumps(PlayerList))
                server.reply(info, '已将%s移除白名单'%(text[2]))
                return
        elif text[1] == 'list':
            nowtime = int(time.time())
            shownum = cfg['PlayerSystemConfig']['WhiteList']['shownum']
            if len(text) == 3:
                paper = int(text[2])
            else:
                paper = 1
            lenght = len(keys)
            text = '白名单列表 现在时间：%s'%(time.strftime('%Y.%m.%d %H:%M:%S', time.localtime(nowtime)))
            for each in keys[(paper-1)*shownum:paper*shownum]:
                text += '\n昵称：%s，上次登录时间：%s'%(each, time.strftime('%Y.%m.%d %H:%M:%S', time.localtime(PlayerList[each]['LastTime'])) if PlayerList[each]['LastTime'] != 0 else '未登录')
            text += '\n白名单列表 共%d条数据 第%d页 共%d页'%(lenght, paper,lenght/6 if lenght/6 == lenght//6 else lenght//6+1)
            if player == None:
                log(server, text)
            else:
                server.tell(player, text)
        else:
            if player == None:
                log(server, '命令错误\n白名单管理命令\n!!WL：显示这条消息\n!!WL add 玩家：添加玩家到白名单\n!!WL del 玩家：删除玩家白名单\n!!WL list [页数]：白名单玩家名单')
            else:
                server.tell(player, '命令错误\n白名单管理命令\n!!WL：显示这条消息\n!!WL add 玩家：添加玩家到白名单\n!!WL del 玩家：删除玩家白名单\n!!WL list [页数]：白名单玩家名单'%text[2])

    if text[0] == '!!log':
        if len(text) == 1:
            server.tell(player, '!!l 密码：登录账号')
            return
        for each in PlayerEvent:
            if each['Name'] == player and each['Type'] == 'Login':
                pwd = hashlib.sha256(PlayerList[player]['Pwd'].join(each['salt']).encode()).hexdigest()
                log(server, pwd)
                if text[1] == pwd:
                    each['Pass'] = True
                    PlayerList[player]['LastTime'] = int(time.time())
                    SavePSD(json.dumps(PlayerList))
                    server.tell(player, cfg['TextConfig']['loginsuccess'])
                    server.tell(player, cfg['TextConfig']['welcome'])
                else:
                    each['Chance'] -= 1
                    server.tell(player, cfg['TextConfig']['pwdwrong'])
                    if each['Chance'] == 0:
                        each['Pass'] = True
                        server.execute('/kick %s %s'%(player, cfg['TextConfig']['Chanceover']))
                        log(server, '%s登录机会用尽，已踢出'%(player))
                break
        else:
            server.tell(player, cfg['TextConfig']['nostate'])
    elif text[0] == '!!PS':
        if len(text) == 1:
            server.reply(info, '!!PS setnewpwd [玩家]：重新设定随机密码')
            return
        if text[1] == 'resetpwd':
            pwd = ''.join(random.sample(string.ascii_letters+string.digits, cfg['PlayerSystemConfig']['Login']['pwdlen']))
            if len(text) == 2:
                if player == None:
                    log(server, '未指定玩家')
                else:
                    for each in PlayerEvent:
                        if each['Name'] == player and each['Type'] == 'Login':
                            server.tell(player, cfg['TextConfig']['nostate'])
                            return
                    PlayerList[player]['Pwd'] = hashlib.md5(pwd.encode()).hexdigest()
                    SavePSD(json.dumps(PlayerList))
                    server.tell(player, cfg['TextConfig']['pwdreset'].replace('{pwd}', pwd).replace('{name}', player))
            elif len(text) == 3:
                if server.get_permission_level(info) >= 3:
                    PlayerList[text[2]]['Pwd'] = hashlib.md5(pwd.encode()).hexdigest()
                    SavePSD(json.dumps(PlayerList))
                    server.reply(info, cfg['TextConfig']['pwdreset'].replace('{pwd}', pwd).replace('{name}', text[2]))
                else:
                    server.tell(player, cfg['TextConfig']['nopermission'])

def on_player_joined(server, player):
    global PlayerList, PlayerEvent
    keys = list(PlayerList.keys())
    if cfg['PlayerSystemConfig']['Login']['enable']:
        if PlayerList.get(player, None) != None:
            if PlayerList[player]['Pwd'] != None:
                if cfg['PlayerSystemConfig']['AutoLogin']['enable']:
                    if int(time.time()) - PlayerList[player]['LastTime'] <= cfg['PlayerSystemConfig']['AutoLogin']['day']*60*60*24:
                        server.tell(player, cfg['TextConfig']['autologin'])
                        server.tell(player, cfg['TextConfig']['welcome'])
                    else:
                        salt = ''.join(random.sample(string.ascii_letters+string.digits, cfg['PlayerSystemConfig']['Login']['saltlen']))
                        PlayerEvent.append({'Name':player, 'Type':'Login', 'Pass':False, 'Chance':cfg['PlayerSystemConfig']['Login']['chance'], 'salt':salt})
                        for each1 in PlayerEvent:
                            if each1['Name'] == player:
                                PlayerEvent.append({'Name':player, 'Type':'Loop', 'Pass':False, 'Text':'/tp %s ~ ~ ~ ~ ~'%(each1['Name'])})
                                PlayerEvent.append({'Name':player, 'Type':'Loop', 'Pass':False, 'Text':'/effect clear %s'%(each1['Name'])})
                                log(server, '%s的密码%s'%(player, salt))
                                for _ in range(int(cfg['PlayerSystemConfig']['Login']['seconds']) // 2):
                                    if each1['Pass']:
                                        PlayerEvent.remove(each1)
                                        for each2 in PlayerEvent:
                                            if each2['Name'] == player and each2['Type'] == 'Loop':
                                                PlayerEvent.remove(each2)
                                        break
                                    server.tell(player, cfg['TextConfig']['login'].replace('{salt}', salt))
                                    time.sleep(2)
                                else:
                                    PlayerEvent.remove(each1)
                                    for each2 in PlayerEvent:
                                        if each2['Name'] == player and each2['Type'] == 'Loop':
                                            PlayerEvent.remove(each2)
                                    server.execute('/kick %s %s'%(player, cfg['TextConfig']['timeover']))
                                    log(server, '%s登录超时，已踢出'%(player))
                else:
                    salt = ''.join(random.sample(string.ascii_letters+string.digits, cfg['PlayerSystemConfig']['Login']['saltlen']))
                    PlayerEvent.append({'Name':player, 'Type':'Login', 'Pass':False, 'Chance':cfg['PlayerSystemConfig']['Login']['chance'], 'salt':salt})
                    for each1 in PlayerEvent:
                        if each1['Name'] == player:
                            PlayerEvent.append({'Name':player, 'Type':'Loop', 'Pass':False, 'Text':'/tp %s ~ ~ ~ ~ ~'%(each1['Name'])})
                            PlayerEvent.append({'Name':player, 'Type':'Loop', 'Pass':False, 'Text':'/effect clear %s'%(each1['Name'])})
                            log(server, '%s的密码%s'%(player, salt))
                            for _ in range(int(cfg['PlayerSystemConfig']['Login']['seconds']) // 2):
                                if each1['Pass']:
                                    PlayerEvent.remove(each1)
                                    for each2 in PlayerEvent:
                                        if each2['Name'] == player and each2['Type'] == 'Loop':
                                            PlayerEvent.remove(each2)
                                            log(server, '%s成功加入游戏'%(player))
                                    break
                                server.tell(player, cfg['TextConfig']['login'].replace('{salt}', salt))
                                time.sleep(2)
                            else:
                                PlayerEvent.remove(each1)
                                for each2 in PlayerEvent:
                                    if each2['Name'] == player and each2['Type'] == 'Loop':
                                        PlayerEvent.remove(each2)
                                server.execute('/kick %s %s'%(player, cfg['TextConfig']['timeover']))
                                log(server, '%s登录超时，已踢出'%(player))
            else:
                pwd = ''.join(random.sample(string.ascii_letters+string.digits, cfg['PlayerSystemConfig']['Login']['pwdlen']))
                PlayerList[player]['Pwd'] = pwd
                PlayerList[player]['LastTime'] = int(time.time())
                SavePSD(json.dumps(PlayerList))
                server.tell(player, cfg['TextConfig']['registersuccess'].replace('{pwd}', pwd))
                server.tell(player, cfg['TextConfig']['welcome'])
                log(server, '%s成功加入游戏'%player)
        else:
            if cfg['PlayerSystemConfig']['WhiteList']['enable']:
                server.execute('/kick %s %s'%(player, cfg['TextConfig']['nowhitelist']))
                log(server, '%s没有白名单尝试加入游戏，已踢出'%player)
            else:
                pwd = ''.join(random.sample(string.ascii_letters+string.digits, cfg['PlayerSystemConfig']['Login']['pwdlen']))
                PlayerList[player] = {'Pwd':pwd, 'LastTime':int(time.time())}
                SavePSD(json.dumps(PlayerList))
                server.tell(player, cfg['TextConfig']['registersuccess'].replace('{name}', player).replace('{pwd}', pwd))
                server.tell(player, cfg['TextConfig']['welcome'])
                log(server, '%s成功加入游戏'%(player))
    else:
        log(server, '%s成功加入游戏'%(player))
        server.tell(player, cfg['TextConfig']['welcome'])

def on_player_left(server, player):
    global PlayerEvent
    for each in PlayerEvent:
        if each['Name'] == player:
            each['Pass'] = True

def on_unload(server):
    global Loop
    Loop = False
