window._cookie = function(){
    /* Read document cookie
    Returns object
    */
    var cookie_obj = {};
    var cookiearray = document.cookie.split("; ");
    for (var i = 0; i < cookiearray.length; i++) {
        cookie_obj[cookiearray[i].split("=")[0]] = decodeURIComponent(cookiearray[i].split("=")[1])
    }
    return cookie_obj
}()

window._cookie_exp = function(){
    var d = new Date();
    d.setFullYear(d.getFullYear() + 10);
    return d.toUTCString();
}()

class socket {
    constructor(url){
        this.ws = new ReconnectingWebSocket(url)
        this.ws.send_queue = Array();
        this.ws.warning_message = false; // Indicates if warning message is open in browser
        this.ws.onmessage = this.recv;
        this.ws.onopen = this.sockopened;
        this.ws.onclose = this.sockclosed;
    }
    send(method, args, kwargs){
        var cmd = {'method': method, 'args': args || [], 'kwargs': kwargs || {}}
        if(this.ws.readyState != 1 && this.ws.warning_message == false){
            this.ws.send_queue.unshift(cmd)
        } else {
            this.ws.send(JSON.stringify(cmd))
        }
    }
    recv(msg){
        var m = JSON.parse(msg.data)
        if(m.command == 'set'){
            try {
                var chain = m.ref.split('.');
                var ref = app;
                for(var i=0; i < chain.length; i++){
                    if(chain[i]){
                        ref = ref['$refs'][chain[i]]
                    }
                }
                for(var k in m.data){
                    ref[k] = m.data[k]
                }
            } catch (err) {
                // console.log('Something Broke: ', err)
            }
        } else if (m.command == 'notify'){
            app.$notify(m.notification)
        } else if (m.command == 'update_movie'){
            try {
                if(app.$refs.view.movies){
                    for(var i=0; i < app.$refs.view.movies.length; i++){
                        if(app.$refs.view.movies[i] && app.$refs.view.movies[i].imdbid == m.imdbid){
                            for(var k in m.data){
                                app.$refs.view.movies[i][k] = m.data[k]
                            }
                            break
                        }
                    }
                }
            } catch (err) {
                //console.log('uhhhhhh', err)
            }
        }
    }
    sockopened(){
        if(this.warning_message){
            this.sock_closed_message.close();
            app.$message({showClose: false, message: 'Reconnected to server.', type: 'success', duration: 1500});
        }
        for(var i=this.send_queue.length - 1; i >= 0; i--){
            this.send(JSON.stringify(this.send_queue[i]))
            this.send_queue.pop();
        }
    }
    sockclosed(){
        if(!this.warning_message){
            this.sock_closed_message = app.$message({showClose: false, message: 'Connection to server lost.', type: 'warning', duration: 0});
            this.warning_message = true;
        }
    }
}

Vue.use(VueLazyload)
Vue.config.devtools = false

templates = {
    'navbar': httpVueLoader('/static/components/navbar.vue'),
    'library': {'status': httpVueLoader('/static/components/library/status.vue'),
                'status_modal': httpVueLoader('/static/components/library/status_modal.vue'),
                'add': httpVueLoader('/static/components/library/add.vue')
                }
}

Vue.component('navbar', templates['navbar']);
Vue.component('status-modal', templates['library']['status_modal'])

router = new VueRouter({
    mode: 'hash',
    base: window.location.href,
    routes: [{path: '/library/status', component: templates['library']['status']},
             {path: '/library/add', component: templates['library']['add']}
            ]
})

app = new Vue({
    el: '#app',
    router: router,
    data: {socket: new socket('ws://localhost:9090/ws')},
    methods:{
        handle_select: function(){}
    }
});
