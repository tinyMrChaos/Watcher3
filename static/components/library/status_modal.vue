<template>
<div id="status_modal">
    <el-row id='confirm_trash'>
        <el-collapse-transition>
            <div v-show="trash_bar_open">
                <el-alert :title="'Trash ' + movie.title + '?'" type="warning" description="more text description" :closable="false" show-icon>
                    <div>
                        <span v-if="movie.finished_file">
                            <el-checkbox v-model="confirm_trash_file"></el-checkbox>
                            Delete file ({{movie.finished_file}})?
                        </span>

                        <el-button class="left" size="mini" type='warning' v-on:click="trash_movie(movie.imdbid)">
                            Trash <i class="mdi mdi-delete"></i>
                        </el-button>
                    </div>
                </el-alert>
            </div>
        </el-collapse-transition>
    </el-row>
    <el-row :gutter="20">
        <el-col :sm="5" :xs="24">
            <img class='poster' :src="'/posters/' + (movie.poster || 'missing_poster.jpg')"/>
        </el-col>
        <el-col :sm="13" :xs="24">
            <div id="modal_tags" class='flex flex-middle flex-between'>
                <el-tag size="mini" type="success" v-if='movie.finished_file'>
                    File: {{movie.finished_file}}
                </el-tag>
                <a :href="'http://www.imdb.com/title/' + movie.imdbid" target='_blank'>
                    <el-tag size="mini">
                        <i class='mdi mdi-link-variant'></i>
                        IMDB
                    </el-tag>
                </a>
                <a :href="'https://www.themoviedb.org/movie/' + movie.tmdbid" target='_blank'>
                    <el-tag size="mini">
                        <i class='mdi mdi-link-variant'></i>
                        TheMovieDB
                    </el-tag>
                </a>
                <el-tag size="mini" type="info">Date Added: {{movie.added_date}}</el-tag>
                <el-tag size="mini" type="info">Source: {{movie.origin}}</el-tag>
                <el-tag size="mini" type="info">
                    <i class="mdi mdi-star"></i>
                    {{movie.score}}
                </el-tag>
                <el-tag size="mini" type="info">
                    Theatrical Release: {{movie.release_date}}
                </el-tag>
                <el-tag size="mini" type="info">Home Release: {{movie.media_release_date || 'Unknown'}}</el-tag>
            </div>
            <p class="plot">{{movie.plot}}</p>
        </el-col>
        <el-col id="actions" :sm="6" :xs="24">
            <div>
                <el-button-group>
                    <el-button title="Search" v-on:click="backlog_search(movie.imdbid)">
                        <i class="mdi mdi-magnify"></i>
                    </el-button>
                    <el-button title="Trash" @click="trash_bar_open = true">
                        <i class="mdi mdi-delete"></i>
                    </el-button>
                </el-button-group>
            </div>
            <div id="modal_settings">
                <div>
                    Quality
                    <el-select v-model="movie.quality" size="small">
                        <el-option v-for="q in qualities" v-bind:key="q" :value="q" >{{q}}</el-option>
                    </el-select>
                </div>
                <div>
                    <el-switch
                        style="display: block"
                        v-model="auto_management"
                        active-text="Automatic"
                        inactive-text="Finished">
                    </el-switch>
                </div>
                <el-button type='success' size="small" v-on:click="save_settings">
                    <i class="mdi mdi-content-save"></i>
                </el-button>

            </div>
        </el-col>
    </el-row>
    <el-row id="search_results">
        <div class='loader' v-if="this.search_results == null" v-loading='true'>
        </div>
        <el-row v-for="release in search_results" :key="release.guid" style="padding: 0 0.5em;">
            <el-col :sm="24">
                {{release.title}}
            </el-col>
            <el-col :sm="18" :xs="24" style="margin: 0.5em 0;">
                <el-tag :class="'status ' + release.status" size="mini" type='info'>
                    {{release.status}}
                </el-tag>
                <el-tag type='info' size='mini'>
                    {{release.type}}
                </el-tag>
                <el-tag type='info' size='mini'>
                    {{release.indexer}}
                </el-tag>
                <el-tag type='info' size='mini'>
                    {{human_file_size(release.size)}}
                </el-tag>
                <el-tag type='info' size='mini'>
                    {{release.score}}
                </el-tag>
            </el-col>
            <el-col :sm="6" :xs="24" style="text-align: center; margin: 0.5em 0;">
                <el-button-group>
                    <el-button title="Info" size="small" v-on:click="window.open(release.info_link, '_blank')">
                        <i class="mdi mdi-information-outline"></i>
                    </el-button>
                    <el-button title="Download" size="small" v-on:click="app.socket.send('download_release', [release, movie.year])">
                        <i class="mdi mdi-arrow-down-bold"></i>
                    </el-button>
                    <el-button title="Mark Bad" size="small">
                        <i class="mdi mdi-cancel"></i>
                    </el-button>
                </el-button-group>
            </el-col>
        </el-row>
    </el-row>
</div>
</template>


<script>

module.exports = {
    data() {
        return {
            auto_management: (this.movie.status != 'Disabled'),
            search_results: null, //null indicates they are loading, an empty array indicates 0 results
            trash_bar_open: false,
            confirm_trash_file: false
        }
    },
    props: {
        movie: Object,
        qualities: Array,
        open: Boolean
    },
    methods: {
        save_settings: function(){
            app.socket.send('set_movie_settings', [this.movie.imdbid, this.auto_management, this.movie.quality])
        },
        human_file_size: function(size){
            var i = Math.floor(Math.log(size) / Math.log(1024));
            return (size / Math.pow(1024, i)).toFixed(2) * 1 + ' ' + ['B', 'kB', 'MB', 'GB', 'TB'][i];
        },
        backlog_search: function(imdbid){
            this.search_results = null;
            app.socket.send('backlog_search', [imdbid]);
        },
        trash_movie: function(imdbid){
            app.socket.send('trash_movie', [imdbid, this.confirm_trash_file])
            this.$parent.$parent.modal_open = false;
        }
    },
    mounted: function(){
        this.auto_management = (this.movie.status != 'Disabled')
    }
}

</script>


<style type="text/css">
#status_modal img.poster{
    width: 100%;
}

#modal_tags > *{
    margin: 2px 2px 2px 0;
}

p.plot{
    margin-bottom: 1em;
}

#actions{
    text-align: center;
}

#modal_settings{
    margin-top: 3em;
}

#modal_settings > *{
    margin-bottom: 1em;
}

#modal_settings button{
    width: 100%;
    max-width: 200px;
}

#search_results{
    max-height: 18em;
    overflow-y: scroll;
    margin: 1.5em 1em 0.5em 1em;
    padding: 0 0.5em;
}

#search_result > div{
    padding: 0 0.5em;
}

#search_results > div:nth-child(odd){
    background: rgba(0,0,0,.05)
}

#search_results .loader{
    height: 5em;
}

#confirm_trash{
    margin-bottom: 1.5em;
}
</style>
