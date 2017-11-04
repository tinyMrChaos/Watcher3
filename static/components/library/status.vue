<template>
<div id="status" class="is-component">
    <el-row type="flex" justify="space-around">
        <el-button-group>
            <el-button icon="el-icon-menu" :type="layout == 'posters' ? 'primary' : null" v-on:click="set_layout('posters')">
            </el-button>
            <el-button type="primary" :type="layout == 'rows' ? 'primary' : null" v-on:click="set_layout('rows')">
                <i class="mdi mdi-view-agenda"></i>
            </el-button>
            <el-button type="primary" :type="layout == 'table' ? 'primary' : null" v-on:click="set_layout('table')">
                <i class="mdi mdi-view-list"></i>
            </el-button>
        </el-button-group>
        <div>
            <el-select v-model="sort_key" v-on:change="set_sort_key">
                <el-option value="sort_title">Title</el-option>
                <el-option value="year">Year</el-option>
            </el-select>
            <el-button v-on:click="toggle_sort_direction($event)">
                <i v-bind:class="'mdi ' + (sort_direction === 'asc' ?  'mdi-arrow-down': 'mdi-arrow-down')"></i>
            </el-button>
        </div>
    </el-row>

    <el-row type="flex" justify="center">
        <el-pagination @current-change="set_page" :current-page="current_page" :page-size="50" :total="movies_len" layout="prev, pager, next, jumper"></el-pagination>
    </el-row>

    <el-row id="movies" type="flex" justify="space-around">
        <template v-for="movie in display_movies" v-if="movie !== null">
            <div v-if="layout == 'posters'" class="card movie_card" v-bind:key="movie.imdbid">
                <img class='poster' v-lazy="'/posters/' + (movie.poster || 'missing_poster.jpg')" @click="open_modal(movie)">
                <div class="card_base">
                    <h4 class='title'>{{movie.title}}</h4>
                </div>
                <div :class="'status ' + movie.status">{{movie.status}}</div>
                <span class="score" color="white" text-color="white"><i class="mdi mdi-star"></i>{{movie.score}}</span>
            </div>
            <div v-if="layout == 'rows'" class="card movie_row" v-bind:key="movie.imdbid" @click="open_modal(movie)">
                <img v-bind:src="'/posters/' + (movie.poster || 'missing_poster.jpg')"/>
            </div>
        </template>
        <div v-if="layout == 'mini'">
            Doesnt exist yet but will be table
        </div>
    </el-row>

    <el-dialog ref="status_modal" id="movie_modal" :title="this.modal.title + ' (' + this.modal.year + ')'" :visible="modal_open" v-on:close="close_modal">
        <status-modal :movie="modal" :qualities="qualities"></status-modal>
    </el-dialog>

</div>

</template>

<script>

module.exports = {
    data(){
        var layout = _cookie.movie_layout || 'posters';
        var msd = _cookie.movie_sort_direction || 'asc';

        return {movies: [],                 // Cached movies from server
                movies_len: 0,              // Total length of movies array
                display_movies: [],
                current_page: 1,            // Current pagination page #
                movies_splice: [],          // Movies to automatically add to this.movies array. [0] = page #, [1] = movies array
                layout: layout,             // Layout style for movies (posters, rows, mini)
                sort_key: _cookie.movie_sort_key || 'sort_title',   // How to sort movies (sort_title, year, status)
                sort_direction: msd,        // Direction to sort movies (asc, desc)
                modal_open: false,          // Is movie modal open? Also triggers opening of modal.
                modal: {},                  // Movie to display in modal
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
        set_page: function(page){
            this.current_page = page;

            var cached_page = this.movies.slice(page * 50 -50, page * 50);
            var cache_complete = true;
            for(var i=0; i < cached_page.length; i++){
                if(cached_page[i] === null){
                    cache_complete = false;
                    break;
                }
            }

            if(!cache_complete){
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
            this.set_cookie('movie_sort_key', key);
        },
        toggle_sort_direction: function(){
            this.sort_direction = {'asc': 'desc', 'desc': 'asc'}[this.sort_direction] || 'asc';
            this.movies.reverse();
            this.set_page(1);
            this.set_cookie('movie_sort_direction', this.sort_direction);
        },
        set_cookie: function(k, v){
            document.cookie = `${k}=${encodeURIComponent(v)};path=/;expires=${_cookie_exp}`;
        },
        open_modal: function(movie){
            app.$refs.status_modal = this.$refs.status_modal;
            this.modal = movie;
            app.socket.send('search_results', [movie.imdbid], {'quality': movie.quality})
            this.modal_open = true;
        },
        close_modal: function(){
            console.log('close_modal')
            this.modal_open = false;
            app.$refs.status_modal = undefined;
        }
    },
    beforeMount: function(){
        app.socket.send('movie_count');
        app.socket.send('movie_page', [this.sort_key, this.sort_direction], {'offset': 0})
    },
    mounted: function(){

    }
}

</script>


<style type="text/css">
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

.status.Waiting{
    background: gray;
}
.status.Wanted{
    background: orange;
}
.status.Found{
    background: yellow;
}
.status.Snatched{
    background: green;
}

.status.Finished{
    background: blue;
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
</style>
