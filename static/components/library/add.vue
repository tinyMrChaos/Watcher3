<template>
<div id="add">
ADD
</div>

</template>

<script>

module.exports = {
    data(){
        var layout = _cookie.movie_layout || 'posters';
        var msd = _cookie.movie_sort_direction || 'asc';

        return {movies: [],
                pages: 1,
                current_page: 1,
                movies_hidden: 0,
                layout: layout,
                sort_key: _cookie.movie_sort_key || 'sort_title',
                movie_sort_direction: msd,
                movie_modal: false,
                modal: {}
                }
    },
    methods: {
        get_movies: function(page){
            /* Gets page of movies
            page (int): page # to get from server

            Splices retrieved movies into this.movies

            Returns array of retrieved movies
            */

            var offset = (page * 50) - 50
            payload = {sort_key: this.sort_key, sort_direction: _cookie.movie_sort_direction || 'asc', limit: 50, offset: offset}
            app.$http.post('/ajax/library', payload).then(response => {
                var t = this.movies.slice(0)
                var a = t.splice(offset)
                a = a.splice(response.data.length)
                t = t.concat(response.data).concat(a)
                this.movies = t
                return response.data
            })
        },
        library_count: function(reset){
            app.$http.post('/ajax/library_count', {}).then(response => {
                if(reset){
                    this.movies = Array(response.data[0])
                }
                this.movies_visible = response.data[0]
                this.movies_hidden = response.data[1]
            });
        },
        movie_page: function(page){
            /* Gets slice of movies to display
            page (int): page of movies to return

            If slice isn't complete calls server for info

            Returns array
            */
            var use_cache = true;
            var offset = (this.current_page * 50) - 50;
            var cached_page = this.movies.slice(offset, offset + 50);

            for(i=0; i < cached_page.length; i++){
                if(cached_page[i] === undefined){
                    use_cache = false;
                    break;
                }
            }

            if(!use_cache){
                return this.get_movies(page);
            } else {
                return cached_page;
            }
        },
        set_page: function(page){
            this.current_page = page;
        },
        set_layout: function(layout){
            this.layout = layout;
            this.set_cookie('movie_layout', layout);
        },
        set_sort_key: function(key){
            this.set_cookie('movie_sort_key', key);
        },
        toggle_sort_direction: function(){
            var s = {'asc': 'desc', 'desc': 'asc'};
            this.movie_sort_direction = s[this.movie_sort_direction] || 'asc';
            this.movies.reverse();
            this.set_page(1);
            this.set_cookie('movie_sort_direction', this.movie_sort_direction);
        },
        set_cookie: function(k, v){
            document.cookie = `${k}=${encodeURIComponent(v)};path=/;expires=${_cookie_exp}`;
        },
        open_modal: function(movie){
            this.modal = movie;
            this.movie_modal = true;
            // TODO: stop body from scrolling
        },
        close_modal: function(){
            // TODO: stop body from scrolling
        },
        socket_send: function(){
            console.log(app.$socket)
        }
    },
    beforeMount: function(){
        this.library_count(true);
        this.get_movies(1);
    },
    socket: {
        events: {

            // Similar as this.$socket.on("changed", (msg) => { ... });
            // If you set `prefix` to `/counter/`, the event name will be `/counter/changed`
            //
            changed(msg) {
                console.log("Something changed: " + msg);
            }

            /* common socket.io events
            connect() {
                console.log("Websocket connected to " + this.$socket.nsp);
            },

            disconnect() {
                console.log("Websocket disconnected from " + this.$socket.nsp);
            },

            error(err) {
                console.error("Websocket error!", err);
            }
            */

        }
    }

}

</script>


<style type="text/css">
.active{
    color: red;
}
div#status{
    padding-top: 4em;
}

div#pager{
    margin-top: 0.5em;
}

.flex{
    flex-wrap: wrap;
}

div#movies *{
    transition: none;
    transition: box-shadow 0.3s;
}

.movie{
    display: inline;
}

.movie .status.Waiting{
    background: gray;
}
.movie .status.Wanted{
    background: orange;
}
.movie .status.Finished{
    background: green;
}


.movie_card{
    width: 12em;
    position: relative;
    border-radius: 4px;
    cursor: pointer;
}
.movie_card img{
    height: 18em;
    width: 100%;
    border-radius: 4px 4px 0 0;
}
.movie_card .status{
    height: 1.5em;
    padding: 0 0.5em;
    display: inline-block;
    border-radius: 0 4px;
    position: absolute;
    bottom: 0;
    left: 0;
}

.movie_card .title{
    width: 100%;
    text-overflow: ellipsis;
    overflow: none;
    padding-bottom: 1.5em;
}
.movie_card .score{
    position: absolute;
    right: 0;
    bottom: 0;
    margin-right: 0.5em;
}

.movie_row{
    width: 48%;
    position: relative;
    border-radius: 4px;
    cursor: pointer;
    padding: 0;
    margin: .5em 0;
    display: inline-block;
}
.movie_row img{
    height: 6em;
    border-radius: 4px 0 0 4px;
    padding: 0;
}
</style>
