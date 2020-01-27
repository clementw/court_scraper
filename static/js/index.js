//首页脚本
// 设想多个姓名、身份证号一起查询，一行编写姓名和身份证号，一行一个
// 现在的问题是移到下班点就变慢了，验证码有时候获取到了但是无法显示，感觉也和网络情况有关
// 详情抓取有时候会出现html标签代码
// 部分人员执行和失信数据时有时无
// (function(){
    var crawlerData={
        shixin:{},
        zhixing:{}
    },
    formData={
        totalshixin:0,
        totalzhixing:0,
        loadshixin:0,
        loadzhixing:0,
        valListshixin:[],//输入的查新信息数组
        valListzhixing:[]

    }
    var crawlerItem={
        "case_id":"--",//编号
        "name":"--",//姓名
        "caseCode":"--",//案号
        "age":"--",//年龄
        "sexy":"--",//性别
        "id_card":"--",//身份证号码
        "partyCardNum":"--",//身份证号码
        "businessEntity":"--",
        "courtName":"--",//执行法院
        "areaName":"--",//省份
        "partyTypeName":"--",
        "gistId":"--",//执行依据文号
        "regDate":"--",//立案时间
        "gistUnit":"--",//做出执行依据单位
        "duty":"--",//生效法律文书确定的义务
        "performance":"--",//被执行人的履行情况
        "performedPart":"--",
        "unperformPart":"--",
        "disruptTypeName":"--",//失信被执行人行为具体情形
        "publishDate":"--",//发布时间
        "execMoney":"--",//执行标的
        "execCourtName":"--"//执行法院
    };
    var HomePage=function(){
        //获取socket对象
        var WebSocket = window.WebSocket || window.MozWebSocket;
        if (WebSocket) {
            try {
                var _host=window.location.host;//获取当前域名
                //创建web socket对象
                this.socket = new WebSocket('ws://'+_host+'/court/socket');
            } catch (e) {}
        }
        this.requestPermission=false;
    }
    HomePage.prototype={
        init:function(){
            var _that=this;
            if(this.socket){
                this.socket.onopen = function(){
                    msg.createUA("shixin");//创建失信UA
                    msg.createUA("zhixing");//创建执行UA
                    msg.getCaptcha("shixin");//获取失信验证码
                    msg.getCaptcha("zhixing");//获取执行验证码
                }
                this.socket.onmessage = function(event){
                    msg.catchMessage(event.data);
                }
            }
            //事件绑定
            this.initBind();
            //判断是否支持通知
            if(window.Notification && Notification.permission !== "denied") {
                Notification.requestPermission(function(status) {    // 请求权限
                    _that.requestPermission=status;
                });
            }
        },
        initBind:function(){
            //查询按钮click事件绑定
            $(".js_dataForm").submit(function(ev){
                var names = $("#usertext").val();
                if(!names){
                    alert("请输入查询条件");
                }
                names = names?names.split(/[\r\n|\n]/):"";
                var code = $(this).find(".js_captcha").val(),
                option = $(this).find(".optionVal").val();
                if(!code){
                    alert("请输入验证码");
                    return;
                }
                for(var i=0;i<names.length;i++){
                    if(!$.trim(names[i])){
                        continue;
                    }
                    formData["valList"+option].push(names[i]);
                    if(formData["valList"+option].length==1){
                        var _strList=$.trim(names[i]).split(/\s+/);
                        msg.getResult(
                            code,
                            _strList[0],
                            _strList[1]||"",
                            option
                        );
                    }
                    formData["total"+option]=formData["total"+option]+1;
                }
                // console.log(formData["valList"+option]);
                //隐藏form表单
                $("#"+option+"_form .form-group").addClass("hide");
                //显示进度条
                $("#"+option+"_form .js_progress_wrap").removeClass("hide");
                //显示查看更多按钮
                $("#showBtn").removeClass("hide");
                return false;
            });
            //刷新验证码
            $(".auth_code").click(function(){
                msg.getCaptcha($(this).data("option"));
            });
            //tab click bind
            $("body").on("click",".nav-tabs li",function(e){
                var index = $(this).index();
                var conts = $(this).parents(".bs-callout").find(".tab-pane");
                var _targetCont=conts.eq(index);
                $(this).parent().find("li").removeClass("active");
                conts.removeClass("active");
                _targetCont.addClass("active");
                $(this).addClass("active");
                e.preventDefault()
            });
            //显示无纪录的
            $("#showBtn").click(function(){
                $(".bs-callout").toggleClass("active");
                $(this).addClass("btn-info")
            });

            $("#dataWrap").on("click",".moreLink",function(){
                var _id=$(this).data("id"),
                _type=$(this).data("type");
                var _element=crawlerData[_type][_id];
                for(var _item in _element){
                    $('#'+_type+'Modal').find("td.js_"+_item).text(_element[_item]);
                }
                $('#'+_type+'Modal').modal("show")
            })

        }
    }


    //Message 相关方法
    var Message=function(){}
    Message.prototype={
        //监控
        catchMessage:function(data){
            //获取返回数据
            jdata = JSON.parse(data);
            if (jdata.type === 'progress') {
                // $("").html('<p>' + jdata.data + '</p>');
            }
            //判断验证码结果
            if (jdata.type === 'captcha_result') {
                var option=jdata.option;
                //验证码通过
                if (jdata.data) {

                    var code = $("#"+option+"_form").find(".js_captcha").val();
                    formData["valList"+option].shift();//去掉第一个元素
                    var _items=formData["valList"+option],len=_items.length;
                    console.log(_items);
                    for(var i=0;i<len;i++){
                        console.log(_items[i]);
                        var _strList=$.trim(_items[i]).split(/\s+/);
                        console.log(_strList[0]);
                        msg.getResult(
                            code,
                            _strList[0],
                            _strList[1]||"",
                            option
                        );
                    }
                    formData["valList"+option]=[];//清空数据
                } else {
                    formData["valList"+option]=[];//清空数据
                    //显示form表单
                    $("#"+option+"_form .form-group").removeClass("hide");
                    //隐藏进度条
                    $("#"+option+"_form .js_progress_wrap").addClass("hide");
                    alert("验证码输入错误，请重新输入");
                    $("#"+option+"_form .js_captcha").focus().val("").parent().addClass('has-error');
                }
            }
            //显示列表
            if (jdata.type === 'result') {
                crawlerList.showList(jdata.data);
            }
            // 显示详情
            if(jdata.type==='detail'){
                try{
                    var _data=jdata.data,//将json字符转换成json
                    key=_data.id+"";
                    _data=$.extend({},crawlerData[_data.option][key],_data);//组合对象
                    crawlerData[_data.option][_data.id]=_data;//添加到公共变量中
                    crawlerList.repaint(_data.option)//开启重绘任务
                }catch(e){
                    console.log(e);
                }
            }
            //显示验证码
            if (jdata.type === 'image') {
                $("#"+jdata.option+"_form .auth_code").html("<img src=\"data:image/jpg;base64, " + jdata.data + "\" />");
            }
            //获取抓取进度    
            if (jdata.type ==='load_progress'){
                var option=jdata.option;

                formData["load"+jdata.option]=formData["load"+option]+1;
                var percent = parseInt(formData["load"+option]/formData["total"+option]*100);
                if(percent!=100){//部分抓取完成显示进度
                    $("#"+option+"_form .progress-bar").text(percent+"%").css({"width":percent+"%"});
                }else{//全部抓取完成
                    $("#"+option+"_form .js_progress_wrap").addClass("hide");
                    $("#"+option+"_form .js_finished").removeClass("hide");
                    //用户同意通知
                    if(homePage.requestPermission=="granted"){
                        var messageStr={
                            "shixin":"失信数据抓取完毕",
                            "zhixing":"执行数据抓取完毕"
                        }
                        // 弹出一个通知
                        var n = new Notification('抓取进度', {
                            body : messageStr[option],
                            icon : 'static/img/notice.png',
                            lang : "zh-CN",
                        });
                        //点击回到当前tab
                        n.onclick=function(e){
                            window.focus()
                            n.close();
                        }
                    }
                }
            }
        },
        //获取验证码
        getCaptcha:function(option){
            homePage.socket.send(JSON.stringify({
                    option:$.trim(option),
                    type:'refreshcaptcha'
                })
            );
        },
        //查询结果
        getResult:function(code,name,cardNum,option){
            homePage.socket.send( JSON.stringify({
                    type:'captcha',//验证码类型
                    data:$.trim(code),//验证码
                    name:$.trim(name),//查询姓名
                    cardNum:$.trim(cardNum),//身份证号码
                    option:$.trim(option)
                })
            )
        },
        //创建ua
        createUA:function(option){
            homePage.socket.send(JSON.stringify({
                    type:"createUA",
                    option:$.trim(option)
                })
            );
        }

    }
    var msg=new Message();

    //爬虫list对象
    var CrawlerList=function(){}
    CrawlerList.prototype={
        showList:function(data){
            var _data=data.cases,
            pMark=data.pMark;
            var _list="";
            if(!$("#"+pMark+"_wrap").length){
                var pMarkList=pMark.split("_");//获取pmark参数
                var userName=pMarkList[0],//获取用户名
                cardNum=pMarkList[1]?pMarkList[1]:"";//获取身份证
                _list='<div class="bs-callout " id="'+pMark+'_wrap">'+
                    '<h3>'+userName+' '+cardNum+'</h3>'+
                    '<div>'+
                        '<ul class="nav nav-tabs" role="tablist">'+
                            '<li class="active">'+
                                '<a>失信</a>'+
                            '</li>'+
                            '<li>'+
                                '<a>执行</a>'+
                            '</li>'+
                        '</ul>'+
                        '<div class="tab-content">'+
                            '<div role="tabpanel" class="tab-pane active js_shixinCont">'+
                                '<div class="loadingWrap">'+
                                    '<img src="static/img/loading.gif" class="loadingImg"/><span>正在加载失信数据</span>'+
                                '</div>'+
                            '</div>'+
                            '<div role="tabpanel" class="tab-pane js_zhixingCont">'+
                                '<div class="loadingWrap">'+
                                    '<img src="static/img/loading.gif" class="loadingImg"/><span>正在加载执行数据</span>'+
                                '</div>'+
                            '</div>'+
                        '</div>'+
                    '</div>'+
                '</div>';
                $("#dataWrap").append(_list);//初始化tab框
            }
            var _target = $("#"+pMark+"_wrap").find(".js_"+data.type+"Cont");//获取相应的tab内容
            if(!_target.data("init")){

                var _dataStr="";
                if(data.type=="shixin"){
                    _dataStr+='<table class="table table-bordered table-striped" >'+
                        '<thead>'+
                            '<tr>'+
                                '<th style="min-width:45px;">编号</th>'+
                                '<th style="min-width:45px;">姓名</th>'+
                                '<th style="min-width:75px;">立案时间</th>'+
                                '<th style="min-width:45px;">案号</th>'+
                                '<th style="min-width:45px;">年龄</th>'+
                                '<th style="min-width:45px;">性别</th>'+
                                '<th style="min-width:75px;">身份证号</th>'+
                                '<th style="min-width:45px;">省份</th>'+
                                '<th style="min-width:45px;">义务</th>'+
                                '<th style="min-width:75px;">履行情况</th>'+
                                '<th style="min-width:75px;">发布时间</th>'+
                                '<th style="min-width:45px;">更多</th>'+
                            '</tr>'+
                        '</thead>'+
                        '<tbody class="datalist">';
                }else if(data.type="zhixing"){
                    _dataStr+='<table class="table table-bordered table-striped" >'+
                        '<thead>'+
                            '<tr>'+
                                '<th style="min-width:45px;">编号</th>'+
                                '<th style="min-width:45px;">姓名</th>'+
                                '<th style="min-width:75px;">立案时间</th>'+
                                '<th style="min-width:75px;">执行法院</th>'+
                                '<th style="min-width:45px;">案号</th>'+
                                '<th style="min-width:75px;">身份证号</th>'+
                                '<th style="min-width:45px;">执行标的</th>'+
                                '<th style="min-width:45px;">更多</th>'+
                            '</tr>'+
                        '</thead>'+
                        '<tbody class="datalist">';
                }
                
                if(_data.length){
                    $("#"+pMark+"_wrap").addClass("bs-callout-danger")
                    _dataStr+=listStr(_data,data.type);
                }else{
                    if(data.type=="shixin"){
                        _dataStr+='<tr><td colspan="13" class="hasno">暂无记录</td></tr>';
                    }else if(data.type=="zhixing"){
                        _dataStr+='<tr><td colspan="8" class="hasno">暂无记录</td></tr>';
                    }
                }
                _dataStr+='</tbody></table>';
                $(_target).html(_dataStr);
                $(_target).data("init",true);
            }else{
                $(_target).find(".datalist").append(listStr(_data,data.type));
            }
            //显示列表
            function listStr(data,type){
                var _str="";
                if(type=="shixin"){//失信数据显示
                    for(var i=0;i<data.length;i++){
                        
                        var _item = $.extend({},crawlerItem,data[i]);
                        console.log(_item);
                        crawlerData[type][_item.case_id]=_item;
                        _str+='<tr id="list_'+_item.case_id+'">'+
                        '<th scope="row" class="js_case_id">'+_item.case_id+'</th>'+//编号
                        '<td class="js_name">'+_item.name+'</td>'+//姓名
                        '<td class="js_case_time">'+_item.case_time+'</td>'+//立案时间
                        '<td class="js_case_name">'+_item.case_name+'</td>'+//案号
                        '<td class="js_age">'+_item.age+'</td>'+//年龄
                        '<td class="js_sexy">'+_item.sexy+'</td>'+//性别
                        '<td class="js_id_card">'+_item.cardNum+'</td>'+//身份证号
                        '<td class="js_areaName">'+_item.areaName+'</td>'+//省份
                        '<td class="js_duty">'+_item.duty+'</td>'+//义务
                        '<td class="js_performance">'+_item.performance+'</td>'+//履行情况
                        '<td class="js_publishDate">'+_item.publishDate+'</td>'+//发布时间
                        '<td><span class="moreLink" data-id="'+_item.case_id+'" data-type="'+type+'">更多</span></td>'+
                        '</tr>';
                    }
                }else if(type="zhixing"){//执行数据显示
                    for(var i=0;i<data.length;i++){
                        var _item = $.extend({},crawlerItem,data[i]);
                        crawlerData[type][_item.case_id]=_item;
                        _str+='<tr id="list_'+_item.case_id+'">'+
                        '<th scope="row" class="js_case_id">'+_item.case_id+'</th>'+//编号
                        '<td class="js_name">'+_item.name+'</td>'+//姓名
                        '<td class="js_case_time">'+_item.case_time+'</td>'+//立案时间
                        '<td class="js_execCourtName">'+_item.case_name+'</td>'+//执行法院
                        '<td class="js_caseCode">'+_item.caseCode+'</td>'+//案号
                        '<td class="js_id_card">'+_item.partyCardNum+'</td>'+//身份证号
                        '<td class="js_execMoney">'+_item.execMoney+'</td>'+//执行标的
                        '<td class="moreLink" data-id="'+_item.case_id+'" data-type="'+type+'">更多</td>'+
                        '</tr>';
                    }
                }
                return _str;
            }
        },
        //刷新信息
        repaint:function(option){
            var _list = crawlerData[option];
            for(var item in _list){
                var _obj=_list[item];
                var _target=$("#list_"+_obj.id);
                for(var v in _obj){
                    _target.find(".js_"+v).text(_obj[v]);
                }
            }
        }
    }
    var crawlerList=new CrawlerList();
    var homePage=new HomePage();
    homePage.init();
// })()

