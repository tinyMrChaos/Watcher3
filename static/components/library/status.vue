<template>
<div id="status">
    <el-row id='view_options' type="flex" justify="space-around">
        <el-button-group>
            <el-button icon="el-icon-menu" :type="layout == 'posters' ? 'primary' : 'default'" v-on:click="set_layout('posters')">
            </el-button>
            <el-button type="primary" :type="layout == 'rows' ? 'primary' : 'default'" v-on:click="set_layout('rows')">
                <i class="mdi mdi-view-agenda"></i>
            </el-button>
            <el-button type="primary" :type="layout == 'mini' ? 'primary' : 'default'" v-on:click="set_layout('mini')">
                <i class="mdi mdi-view-list"></i>
            </el-button>
        </el-button-group>
        <div>
            <el-select v-model="sort_key" v-on:change="set_sort_key">
                <el-option value="sort_title" label="Title">Title</el-option>
                <el-option value="year" label="Year">Year</el-option>
                <el-option value="status" label="Status">Status</el-option>
            </el-select>
            <el-button v-on:click="toggle_sort_direction($event)">
                <i v-bind:class="'mdi ' + (sort_direction === 'asc' ?  'mdi-arrow-up': 'mdi-arrow-down')"></i>
            </el-button>
            <el-button v-on:click="refresh_page" title='Refresh Page' size='mini'>
                <i class="mdi mdi-autorenew"></i>
            </el-button>
        </div>
    </el-row>

    <el-row type="flex" justify="center">
        <el-pagination @current-change="set_page" :current-page="current_page" :page-size="50" :total="movies_len" layout="prev, pager, next, jumper"></el-pagination>
    </el-row>

    <el-row id="movies" type="flex" justify="space-around">
        <template v-for="movie in display_movies" v-if="movie !== null">
            <div v-if="layout == 'posters'" class="card movie_card" v-bind:key="movie.imdbid" v-on:click="modal_open = true; modal_movie = movie">
                <img class='poster' v-lazy="'/posters/' + (movie.poster || 'missing_poster.jpg')">
                <div class="card_base">
                    <h4 class='title'>{{movie.title}}</h4>
                </div>
                <div :class="'status ' + movie.status">{{movie.status == 'Disabled' ? 'Finished' : movie.status}}</div>
                <span class="score" color="white" text-color="white"><i class="mdi mdi-star"></i>{{movie.score}}</span>
            </div>
            <div v-if="layout == 'rows'" class="card movie_row" v-bind:key="movie.imdbid" v-on:click="modal_open = true; modal_movie = movie">
                <img v-bind:src="'/posters/' + (movie.poster || 'missing_poster.jpg')"/>
            </div>
            <div v-if="layout == 'mini'" class='movie_mini' v-bind:key='movie.imdbid' v-on:click="modal_open = true; modal_movie = movie">
                <div :class="'mini_status status ' + movie.status" :title='movie.status'></div>
                <span>{{movie.title}}</span>
                <span class='year'>{{movie.year}}</span>
            </div>
        </template>
    </el-row>

    <el-dialog id="movie_modal" :title="this.modal_movie.title + ' (' + this.modal_movie.year + ')'" :visible="modal_open" v-on:open="modal_opened" v-on:close="modal_closed">
        <component ref='status_modal' :is="this.modal_open ? 'status-modal' : null" :open="this.modal_open.sync" :movie="modal_movie" :qualities="qualities"></component>
    </el-dialog>

</div>

</template>

<script>

module.exports = {
    data(){
        return {movies: [],                 // Cached movies from server
                movies_len: 0,              // Total length of movies array
                display_movies: [],
                current_page: 1,            // Current pagination page #
                movies_splice: [],          // Movies to automatically add to this.movies array. [0] = page #, [1] = movies array
                layout: _cookie.movie_layout || 'posters',             // Layout style for movies (posters, rows, mini)
                sort_key: _cookie.movie_sort_key || 'sort_title',   // How to sort movies (sort_title, year, status)
                sort_direction: _cookie.movie_sort_direction || 'asc',        // Direction to sort movies (asc, desc)
                modal_open: false,          // Is movie modal open? Also triggers opening of modal.
                modal_movie: {},                  // Movie to display in modal
                movies_hidden: 0,           // # of movies hidden (Finished or Disabled) if user has hidefinished enabled
                qualities: []
                }
    },
    watch: {
        movies: function(n){
            this.display_movies = this.movies.slice(this.current_page * 50 - 50, this.current_page * 50)
        },
        movies_len: function(n){
            this.movies = Array(n).fill(null);
        },
        movies_splice: function(n){
            // splices requested movies into this.movies
            // n[0] = int page num, n[1] = array of movie objs
            var offset = (n[0] * 50) - 50
            var m = this.movies.slice(0)
            var pre_cut = m.splice(0, offset)
            var post_cut = m.splice(n[1].length)
            this.movies = pre_cut.concat(n[1]).concat(post_cut)
        }
    },
    methods: {
        set_page: function(page, skip_check){
            this.current_page = page;

            if(!skip_check){
                console.log('checking')
                var cached_page = this.movies.slice(page * 50 - 50, page * 50);
                console.log(cached_page)
                var cache_complete = true;
                for(var i=0; i < cached_page.length; i++){
                    if(cached_page[i] === null){
                        cache_complete = false;
                        break;
                    }
                }
            }

            if(!cache_complete || skip_check == true){
                app.socket.send('movie_page', [this.sort_key, this.sort_direction], {'offset': page * 50 - 50})
            } else {
                this.display_movies = this.movies.slice(page * 50 - 50, page * 50)
            }

        },
        set_layout: function(layout){
            this.layout = layout;
            this.set_cookie('movie_layout', layout);
        },
        set_sort_key: function(key){
            this.movies = Array(this.movies.length).fill(null);
            this.set_cookie('movie_sort_key', key);
            this.set_page(1);
        },
        toggle_sort_direction: function(){
            this.sort_direction = {'asc': 'desc', 'desc': 'asc'}[this.sort_direction] || 'asc';
            this.movies.reverse();
            this.set_page(1);
            this.set_cookie('movie_sort_direction', this.sort_direction);
        },
        refresh_page: function(){
            app.socket.send('movie_count');
            this.set_page(this.current_page, true);
        },
        set_cookie: function(k, v){
            document.cookie = `${k}=${encodeURIComponent(v)};path=/;expires=${_cookie_exp}`;
        },
        modal_opened: function(){
            app.socket.send('search_results', [this.modal_movie.imdbid], {'quality': this.modal_movie.quality})
            app.socket.send('qualities');
        },
        modal_closed: function(){
            this.trash_modal_open = false;
            this.modal_open = false;

        }
    },
    beforeMount: function(){
        app.socket.send('movie_count');
        app.socket.send('movie_page', [this.sort_key, this.sort_direction], {'offset': 0})
    },
    mounted: function(){
        this.name == 'status'
    }
}

</script>


<style type="text/css">
#view_options{
    padding-top: 0.5em;
}
#view_options > div{
    text-align: center;
    margin-bottom: 1em;
}

#view_options div.el-select{
    width: 50%;
}

img.poster{
    display: inline-block;
}
h4{
    text-align: center;
    padding: 0;
    margin: 0;
}
.active{
    color: red;
}

div#pager{
    margin-top: 0.5em;
}

.flex{
    flex-wrap: wrap;
}

div#movies *{
    transition: none;
    transition-property: box-shadow, opacity;
    transition-duration: 0.3s, 0.5s;
}

.movie{
    display: inline;
}

.movie_card{
    width: 12em;
    position: relative;
    border-radius: 4px;
    cursor: pointer;
    font-size: .9em;
}
.movie_card img{
    height: 18em;
    width: 100%;
    border-radius: 4px 4px 0 0;
}
.movie_card .status{
    height: 1.5em;
    line-height: 1.5em;
    padding: 0 0.5em;
    display: inline-block;
    border-radius: 0 4px;
    position: absolute;
    bottom: 0;
    left: 0;
    font-size: 0.9em;
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
    margin: 0 0.5em 0.25em 0;
    font-size: 0.9em;
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

.movie_mini{
    width: 46%;
    padding: 0.25em 1%;
    margin: 0 1%;
    cursor: pointer;
}

.movie_mini:nth-child(4n+1),
.movie_mini:nth-child(4n+2){
    background: rgba(0,0,0,.05)
}

.mini_status{
    display: inline-block;
    height: .75em;
    width: .75em;
    line-height: 1em;
    border-radius: 4px;
}

.movie_mini .year{
    font-size: 0.75em;
    float: right;
}
</style>
