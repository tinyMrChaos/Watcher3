<template>
<div id="status_modal">
    <el-row :gutter="20">
        <el-col :sm="5" :xs="24">
            <img class='poster' :src="'/posters/' + (movie.poster || 'missing_poster.jpg')"/>
        </el-col>
        <el-col :sm="13" :xs="24">
            <div id="modal_tags" class='flex flex-middle flex-between'>
                <el-tag size="mini" type="info" v-if='movie.finished_file'>
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
                    <el-button title="Search">
                        <i class="mdi mdi-magnify"></i>
                    </el-button>
                    <el-button title="Update Metadata">
                        <i class="mdi mdi-tag"></i>
                    </el-button>
                    <el-button title="Trash">
                        <i class="mdi mdi-delete"></i>
                    </el-button>
                </el-button-group>
            </div>
            <div id="modal_settings">
                <div>
                    Quality
                    <el-select v-model="movie.quality">
                        <el-option v-for="q in qualities" v-bind:key="q" :value="q" >{{q}}</el-option>
                    </el-select>
                </div>
                <div>
                    Management
                    <el-select :value="management[movie.status]">
                        <el-option value="Automatic">Automatic</el-option>
                        <el-option value="Disabled">Finished</el-option>
                    </el-select>
                </div>
                <el-button type='success' size="small">
                    <i class="mdi mdi-content-save"></i>
                </el-button>

            </div>
        </el-col>

    </el-row>
    <el-row id="search_results">
        <el-row v-for="release in app.$refs.status_modal.search_results" :key="release.guid">
            <el-col :sm="24">
                {{release.title}}
            </el-col>
            <el-col :sm="12" :xs="12">
                <span :class="'status' + release.status">
                    {{release.status}}
                </span>
            </el-col>
            <el-col :sm="12" :xs="24">
                <el-button-group>
                    <el-button title="Info" size="small">
                        <i class="mdi mdi-magnify"></i>
                    </el-button>
                    <el-button title="Download" size="small">
                        <i class="mdi mdi-tag"></i>
                    </el-button>
                    <el-button title="Trash" size="small">
                        <i class="mdi mdi-delete"></i>
                    </el-button>
                </el-button-group>
            </el-col>
        </el-row> -->
    </el-row>
</div>
</template>


<script>

module.exports = {
    data(){
        return {management: {'Waiting': 'Automatic',
                             'Wanted': 'Automatic',
                             'Found': 'Automatic',
                             'Snatched': 'Automatic',
                             'Finished': 'Automatic',
                             'Disabled': 'Disabled',
                              },
                qualities: [],
                search_results: []
        }
    },
    props: {
        movie: Object,
        qualities: Array,

    },
    mounted: function(){
        app.socket.send('qualities');
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

#actions{
    text-align: center;
}

#modal_settings{
    margin-top: 1.25em;
}

#modal_settings > *{
    margin-bottom: 0.5em;
}

#modal_settings button{
    width: 100%;
    max-width: 200px;
}

#search_results{
    max-height: 18em;
    overflow-y: scroll;
    margin: 1em 1em 0 1em;
    padding: 0.5em;
}

#search_results > div:nth-child(even){
    background: rgba(0,0,0,.05)
}

</style>
