import os
import sys
import time
import subprocess
import ctypes
from playwright.sync_api import sync_playwright

def prevent_sleep():
    """阻止系统休眠和屏幕关闭"""
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001 | 0x00000002)
    except:
        pass

def allow_sleep():
    """恢复正常休眠策略"""
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
    except:
        pass

JS_CODE = r"""
(function() {
    window._botMasterKey = (window._botMasterKey || 0) + 1;
    var myKey = window._botMasterKey;
    
    if(location.href.indexOf('recommend') === -1 && location.href.indexOf('geek') === -1) {
        location.href = 'https://www.zhipin.com/web/chat/recommend';
        return 'NAVIGATING';
    }
    
    if(window._botRunning) return 'ALREADY_RUNNING:' + (window._botTotalClicked || 0);
    
    window._botLimitReached = false;
    window._botTotalClicked = window._botTotalClicked || 0;
    window._botRunning = true; 
    window._botLog = window._botLog || [];
    window._botCurrentJobType = null;
    
    window._botConfig = {
        name: '初始化自动检测...', ageMax: 35, targetExpMin: 0, targetExpMax: 99, targetSalaryMin: 0, targetSalaryMax: 999,
        eduRequire: [], eduExclude: [], targetSales: false, excludeNonSales: false,
        minorLangReq: [], excludeForeigner: false, requireFemale: false, excludeFemale: true, customCheck: null
    };

    function updateConfig() {
        var nt = 'ru_assistant';
        if(window._botCurrentJobType !== nt) {
            window._botCurrentJobType = nt;
            window._botConfig = {
                name: '俄语销售助理', ageMax: 29, targetExpMin: 0, targetExpMax: 99, targetSalaryMin: 0, targetSalaryMax: 999,
                eduRequire: ['本科', '统招', '一本', '二本', '硕士', '博士'], 
                eduExclude: ['大专', '专科', '非统招', '成考', '自考', '26届', '2026届'],
                targetSales: false, excludeNonSales: false, minorLangReq: ['俄语'], 
                excludeForeigner: false, requireFemale: true, excludeFemale: false,
                customCheck: function(f) {
                    var kw = ['外贸', '跨境', '海外', '出口', '国际贸易', 'B2B', '外销'], pf = false;
                    for(var i=0; i<kw.length; i++) {
                        if(f.indexOf(kw[i]) > -1) { pf = true; break; }
                    }
                    if(!pf) return '无外贸相关经验';
                    if(f.indexOf('深圳') === -1) return '不在深圳(需人工核对)';
                    return null;
                }
            };
            window._botLog.push('[自动检测] 识别到职位切换，已自适应变更为 [' + window._botConfig.name + '] 模式');
        }
    }
    
    function getDoc() {
        var mainCards = document.querySelectorAll('li.card-item,li.candidate-card-box,[class*=recommend-card],[class*=geek-item],li[class*=card]');
        if(mainCards.length > 0) return document;
        try {
            var iframe = document.querySelector('iframe');
            if(iframe && iframe.contentDocument) {
                var iCards = iframe.contentDocument.querySelectorAll('li.card-item,li.candidate-card-box,[class*=recommend-card],[class*=geek-item],li[class*=card]');
                if(iCards.length > 0) return iframe.contentDocument;
            }
        } catch(e) {}
        return document;
    }
    
    if(window._botPopupTimer) clearInterval(window._botPopupTimer);
    window._botPopupTimer = setInterval(function() {
        window._botMasterKey = (window._botMasterKey || 0) + 1;
        var myKey = window._botMasterKey;
        var bodyText = document.body ? document.body.innerText : '';
        if(bodyText.indexOf('达上限') > -1 || bodyText.indexOf('今日已达') > -1 || bodyText.indexOf('额度用完') > -1 || bodyText.indexOf('频繁') > -1) {
            window._botLimitReached = true;
        }
        document.querySelectorAll('[class*=dialog] button,[class*=modal] button,[class*=popup] button').forEach(function(b) {
            var t = (b.textContent || '').trim();
            if(t === '关闭' || t === '知道了' || t === '我知道了' || t === '确定') b.click();
        });
    }, 2000);
    
    function scheduleNext(delay) {
        if(window._botLogicTimer) clearTimeout(window._botLogicTimer);
        window._botLogicTimer = setTimeout(runLoop, delay);
    }

    function runLoop() {
        if (window._botMasterKey !== myKey) return; 
        try { _runLoopCore(); } catch(e) { window._botLog.push('[错误] ' + e.message); scheduleNext(3000); }
    }
    function _runLoopCore() {
        if(window._botLimitReached || window._botTotalClicked >= 100) {
            clearInterval(window._botPopupTimer);
            window._botRunning = false;
            return;
        }

        updateConfig();
        var doc = getDoc();
        var cards = doc.querySelectorAll(
            'li.card-item, li.candidate-card-box, [class*=recommend-card], [class*=geek-item-wrap], [class*=geek-item]:not([class*=icon]), li[class*=card], .friend-item, [class*=friend-item]'
        );
        var clicked = false;
        
        for(var i = 0; i < cards.length; i++) {
            var card = cards[i];
            if(card.dataset.botDone) continue; 
            
            var cardText = (card.textContent || '').replace(/\s+/g, ' ');
            var activeEl = card.querySelector('.active-time, [class*="active"]');
            var activeText = activeEl ? (activeEl.textContent || '').trim() : '';
            var nameEl = card.querySelector('.name, [class*="name"]');
            var name = nameEl ? (nameEl.textContent || '').trim() : '';
            if(!name) { var m = cardText.match(/[\u4e00-\u9fa5]{2,4}/); name = m ? m[0] : cardText.substring(0,8); }
            
            var fullInfo = cardText + ' ' + activeText;
            var skipReason = null;
            
            var isActive = fullInfo.indexOf('刚刚') > -1 || fullInfo.indexOf('今日') > -1 || 
                           fullInfo.indexOf('今天') > -1 || fullInfo.indexOf('在线') > -1 || 
                           fullInfo.indexOf('昨') > -1 || fullInfo.indexOf('1日内') > -1 ||
                           fullInfo.indexOf('2日内') > -1 || fullInfo.indexOf('3日内') > -1 ||
                           fullInfo.indexOf('1天内') > -1 || fullInfo.indexOf('2天内') > -1 || fullInfo.indexOf('3天内') > -1 ||
                           /\d{1,2}:\d{2}/.test(fullInfo);
            if(!isActive) skipReason = "非3日内活跃";

            if(!skipReason) {
                var isFemaleIcon = !!card.querySelector('.icon-female, [class*=female]');
                var hasFemaleWord = fullInfo.indexOf('女') > -1 && fullInfo.indexOf('生女') === -1;
                var femaleNameChars = '丽芳华霞梅婷娟英敏玲娜燕珊莉倩竹雪琳瑶珍秀兰莺菊凤翠玉莲红蕊彩素云彩春萍荣琴菁慧佳颖筠巧嫣娥莎茜烨';
                var nameHasFemaleChar = false;
                if(name) {
                    for(var ci=0; ci<name.length; ci++) {
                        if(femaleNameChars.indexOf(name[ci]) > -1) { nameHasFemaleChar = true; break; }
                    }
                }
                if(isFemaleIcon || hasFemaleWord || nameHasFemaleChar) skipReason = "性别女性";
            }

            if(!skipReason) {
                var ageMatch = fullInfo.match(/(\d{2})岁/);
                var age = ageMatch ? parseInt(ageMatch[1]) : 0;
                if(age > window._botConfig.ageMax) skipReason = "年龄超标(" + age + ")";
                if(age === 0 && fullInfo.indexOf('经验') === -1) skipReason = "信息不全(无年龄)";
            }

            if(!skipReason) {
                var goodEdu = false;
                for(var _i=0; _i<window._botConfig.eduRequire.length; _i++){
                    if(fullInfo.indexOf(window._botConfig.eduRequire[_i]) > -1) { goodEdu = true; break; }
                }
                var badEdu = false;
                for(var _j=0; _j<window._botConfig.eduExclude.length; _j++){
                    if(fullInfo.indexOf(window._botConfig.eduExclude[_j]) > -1) { badEdu = true; break; }
                }
                if(!goodEdu || badEdu) skipReason = "学历不符";
            }

            if(!skipReason) {
                if(fullInfo.indexOf('应届') > -1 || fullInfo.indexOf('在校') > -1) skipReason = "应届在校生";
                else {
                    var expMatch = fullInfo.match(/(\d+)\s*[-]?\s*(\d+)?\s*年/);
                    if(!expMatch) {
                         var expMatch2 = fullInfo.match(/(\d+)/);
                         var expStr = expMatch2 ? parseInt(expMatch2[1]) : 0;
                         if(expStr > 0) {
                            if(expStr < window._botConfig.targetExpMin || expStr > window._botConfig.targetExpMax) skipReason = "经验不符(" + expStr + "年)";
                         } else if(window._botConfig.targetExpMin > 0) {
                            skipReason = "无法识别经验年限";
                         }
                    } else {
                        var expMin = parseInt(expMatch[1]);
                        var expMax = expMatch[2] ? parseInt(expMatch[2]) : expMin;
                        if(expMax < window._botConfig.targetExpMin || expMin > window._botConfig.targetExpMax) {
                            skipReason = "经验不符(" + expMin + "-" + (expMatch[2]?expMax:"") + "年)";
                        }
                    }
                }
            }

            if(!skipReason) {
                var salMatch = fullInfo.match(/(\d+)\s*-\s*(\d+)K/i);
                if(salMatch) {
                    var salMin = parseInt(salMatch[1]);
                    var salMax = parseInt(salMatch[2]);
                    if(salMax < window._botConfig.targetSalaryMin || salMin > window._botConfig.targetSalaryMax) {
                        skipReason = "薪资不符(" + salMin + "-" + salMax + "K)";
                    }
                }
            }

            if(!skipReason && window._botConfig.excludeNonSales) {
                var nonSalesKw = ['设计师','UI','UX','平面','插画','摄影','剪辑','后端','前端','程序员','开发工程师', '采购','供应链','仓储','物流','财务','会计','审计','出纳','人事','HR','招聘', '行政','运营','电商运营','内容运营','数据分析','法务','翻译','客服','售后'];
                for(var ni=0; ni<nonSalesKw.length; ni++) {
                    if(fullInfo.indexOf(nonSalesKw[ni]) > -1) { skipReason = '非销售岗位(' + nonSalesKw[ni] + ')'; break; }
                }
            }
            if(!skipReason && window._botConfig.targetSales) {
                var salesKw = ['销售','业务','BD','客户经理','sales','Sales','外贸业务','业务员','销售代表', '销售经理','大客户','开发客户','客户开发','招商','商务'];
                var hasSales = false;
                for(var si=0; si<salesKw.length; si++) {
                    if(fullInfo.indexOf(salesKw[si]) > -1) { hasSales = true; break; }
                }
                if(!hasSales) skipReason = '非销售相关';
            }

            if(!skipReason && window._botConfig.excludeForeigner) {
                var westernNames = ['Mike','Michael','John','James','David','Chris','Tom','Peter','Paul','Mark', 'Kevin','Brian','Eric','Jack','Sean','Ryan','Jason','Adam','Alex','Robert', 'Lisa','Emma','Anna','Julia','Sophie','Maria','Laura','Sarah','Kate','Amy', 'Linda','Emily','Jessica','Christina','Nicole','Jennifer','Stephanie'];
                var isPureLatin = /^[A-Za-z][a-zA-Z .·]{2,}$/.test(name);
                var hasWesternFirst = westernNames.some(function(n){ return name.indexOf(n) === 0; });
                if(isPureLatin || hasWesternFirst) skipReason = "疑似外国人(" + name + ")";
            }

            if(!skipReason && typeof window._botConfig.customCheck === 'function') {
                var cResult = window._botConfig.customCheck(fullInfo);
                if(cResult) skipReason = cResult;
            }
            
            if(skipReason) {
                var entry = '[SKIP] ' + name + ' → ' + skipReason;
                window._botLog.push(entry);
                if(window._botLog.length > 200) window._botLog.shift();
                card.dataset.botDone = 'skip-' + skipReason;
                continue;
            }
            
            var greetBtn = card.querySelector('button.btn-greet, button.btn-chat');
            if(!greetBtn) {
                var allBtns = card.querySelectorAll('button, span.btn-doc');
                for(var j=0; j<allBtns.length; j++) {
                    var bText = (allBtns[j].textContent || '').trim(); if(bText === '打招呼' || bText === '开聊' || bText === '继续沟通') { greetBtn = allBtns[j]; break; }
                }
            }
            
            if(greetBtn) {
                card.dataset.botDone = 'greeted';
                card.scrollIntoView({behavior: 'smooth', block: 'center'});
                
                var clickDelay = 300 + Math.floor(Math.random() * 300);
                setTimeout(function(btn) { try { btn.click(); } catch(e){} }, clickDelay, greetBtn);
                
                window._botTotalClicked++;
                var greetEntry = '[✅ 打招呼] ' + name + ' (累计' + window._botTotalClicked + ')';
                window._botLog.push(greetEntry);
                if(window._botLog.length > 200) window._botLog.shift();
                clicked = true;
                scheduleNext(3000 + Math.floor(Math.random() * 5000)); 
                break;
            } else {
                card.dataset.botDone = 'no-btn';
            }
        }
        
        if(!clicked) {
            try {
                var ifr = document.querySelector('iframe');
                var iWin = ifr ? ifr.contentWindow : window;
                iWin.scrollBy(0, 1200);
                var scrollEntry = '[↓ 滚动] 当页已处理完，加载更多...';
                window._botLog.push(scrollEntry);
                if(window._botLog.length > 200) window._botLog.shift();
            } catch(e) {}
            scheduleNext(1000);
        }
    }

    scheduleNext(500);
    return 'BOT_INJECTED_SUCCESS';
})();
"""

def main():
    print("================================================")
    print("  🤖 Boss 直聘严格打招呼机器人 (Windows版) 启动")
    print("  按 Ctrl+C 可随时停止")
    print("================================================")
    print("(已开启防休眠模式，直到任务完成前电脑不会熄屏)")
    prevent_sleep()
    
    user_data_dir = os.path.join(os.environ['LOCALAPPDATA'], 'BossBotChromeProfile')
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.join(os.environ['LOCALAPPDATA'], r"Google\Chrome\Application\chrome.exe")
    ]
    
    chrome_path = None
    for p in chrome_paths:
        if os.path.exists(p):
            chrome_path = p
            break
            
    if not chrome_path:
        print("未找到 Chrome 浏览器，请确保已安装 Google Chrome！")
        allow_sleep()
        return
        
    print("正在启动 Chrome (独立配置，与主浏览器互不影响)...")
    subprocess.Popen([
        chrome_path,
        "--remote-debugging-port=9222",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "https://www.zhipin.com/web/chat/recommend"
    ])
    
    time.sleep(4)
    
    with sync_playwright() as p:
        try:
            print("连接到浏览器...")
            browser = p.chromium.connect_over_cdp("http://localhost:9222")
        except Exception as e:
            print(f"无法连接到 Chrome: {e}")
            allow_sleep()
            return
            
        contexts = browser.contexts
        if not contexts:
            print("未找到浏览器上下文")
            allow_sleep()
            return
            
        page = contexts[0].pages[-1] if contexts[0].pages else None
        for p in contexts[0].pages:
            try:
                if "zhipin.com" in p.url:
                    page = p
                    break
            except:
                pass
                
        if page:
            try:
                page.bring_to_front()
            except:
                pass
        
        print("\n-------------------------------------------------")
        print(" 👉 请在弹出的 Chrome 浏览器中扫描登录 Boss 直聘")
        print(" 👉 登录后会自动跳转并开始执行任务...")
        print("-------------------------------------------------")
        
        while True:
            try:
                current_url = page.url
                if "login" in current_url or "captcha" in current_url:
                    time.sleep(3)
                elif "recommend" in current_url or "geek" in current_url:
                    time.sleep(2)
                    if "login" not in page.url:
                        break
                else:
                    try:
                        page.goto("https://www.zhipin.com/web/chat/recommend", wait_until="commit")
                    except:
                        pass
                    time.sleep(3)
            except:
                time.sleep(2)
                
        print("\n✅ 成功进入页面，正在注入脚本逻辑...")
        
        try:
            res = page.evaluate(JS_CODE)
            if res.startswith("ALREADY_RUNNING"):
                print("机器人已在运行中...")
            else:
                print("✅ 注入成功！机器人工作在后台进行。")
        except Exception as e:
            print(f"注入失败: {e}")
            allow_sleep()
            return
            
        print("监控中...")
        last_total = 0
        while True:
            time.sleep(3)
            try:
                alive = page.evaluate("typeof window._botRunning !== 'undefined'")
                if not alive:
                    print("\n[系统] 检测到页面刷新，正在重新注入逻辑...")
                    page.evaluate(JS_CODE)
                    time.sleep(2)
                    continue

                logs = page.evaluate("(function(){ var logs = window._botLog || []; window._botLog = []; return logs; })()")
                if logs:
                    for log in logs:
                        print(f"[{time.strftime('%H:%M:%S')}] {log}")
                        
                status = page.evaluate("(function(){ return (window._botRunning===false ? 'DONE:' : 'RUNNING:') + (window._botTotalClicked || 0); })()")
            except Exception as e:
                time.sleep(2)
                continue
                
            total = int(status.split(":")[1]) if ":" in str(status) else last_total
            if total != last_total:
                last_total = total
                
            print(f"\r[进度] 打招呼: {total} / 100   ", end="", flush=True)
            
            if str(status).startswith("DONE"):
                print("\n================================================")
                print(f"🎉 任务完成！本次成功发招呼 {total} 次。")
                print("将在 10 秒后休眠电脑...")
                print("================================================")
                time.sleep(10)
                allow_sleep()
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                break
                
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n结束运行。")
        allow_sleep()
{ var logs = window._botLog || []; window._botLog = []; return logs; })()")
                if logs:
                    with open(log_file_path, "a", encoding="utf-8") as f:
                        for log in logs:
                            log_msg = f"[{time.strftime('%H:%M:%S')}] {log}"
                            print(log_msg)
                            f.write(log_msg + "\n")
                        
                status = page.evaluate("(function(){ return (window._botRunning===false ? 'DONE:' : 'RUNNING:') + (window._botTotalClicked || 0); })()")
            except Exception as e:
                time.sleep(2)
                continue
                
            total = int(status.split(":")[1]) if ":" in str(status) else last_total
            if total != last_total:
                last_total = total
                
            print(f"\r[进度] 打招呼: {total} / 100   ", end="", flush=True)
            
            if str(status).startswith("DONE"):
                print("\n================================================")
                print(f"🎉 任务完成！本次成功发招呼 {total} 次。")
                print("将在 10 秒后休眠电脑...")
                print("================================================")
                with open(log_file_path, "a", encoding="utf-8") as f:
                     f.write(f"[{time.strftime('%H:%M:%S')}] 🎉 任务完成！本次成功发招呼 {total} 次。\n")
                     f.write("================================================\n")
                time.sleep(10)
                allow_sleep()
                os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                break
                
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n结束运行。")
        allow_sleep()
