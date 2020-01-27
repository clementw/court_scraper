//web worker
var crawlerData={},
crawlerItem={
    "case_id":"--",//编号
    "name":"--",//姓名
    "caseCode":"--",//案号
    "age":"--",//年龄
    "sexy":"--",//性别
    "cardNum":"--",//身份证号码
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
    "publishDate":"--"//发布时间
};
var $progress = $('#progress');
var $msg = $('#msg');
var $usertext = $('#usertext');//查询的姓名
var $captchatext = $('#captcha_text');
var $courttype = $('#courttype');//查询类型
// onmessage = function(evt){
    //获取socket对象
    var WebSocket = window.WebSocket || window.MozWebSocket;
    if (WebSocket) {
        try {
            //创建web socket对象
            var socket = new WebSocket('ws://localhost:8000/court/socket');
        } catch (e) {}
    }

    if (socket) {
        //监控
        socket.onmessage = function(event) {
            postMessage(event)

            // //获取返回数据
            // jdata = JSON.parse(event.data);
            // if (jdata.type === 'progress') {
            //     $progress.html('<p>' + jdata.data + '</p>');
            // }
            // //判断验证码结果
            // if (jdata.type === 'captcha_result') {
            //     //验证码通过
            //     if (jdata.data) {
            //         $progress.html('<p>验证码通过</p>');
            //     } else {
            //         $progress.html('<p>验证码错误</p>');
            //     }
            // }
            // //显示列表
            // if (jdata.type === 'result') {
            //     // var _data=syntaxHighlight(jdata.data);
            //     var _data=jdata.data.cases;
            //     var _list="";
            //     for(var i=0;i<_data.length;i++){
            //         _list+='<tr><th scope="row">'+_data[i].case_id+'</th><td>'+_data[i].name+'</td><td>'+_data[i].case_time+'</td><td>'+_data[i].case_name+'</td><td>更多</td></tr>';
            //     }
            //     // $("#datalist").append(_list);
            //     // $msg.html('<p>' + syntaxHighlight(jdata.data) + '</p>');
            // }
            // // 显示详情
            // if(jdata.type==='detail'){
            //     // console.log(jdata);
            // }
            // //显示验证码
            // if (jdata.type === 'image') {
            //     $('#captcha').html( "<img src=\"data:image/jpg;base64, " + jdata.data + "\" />" );
            // }
        }
    }
// }