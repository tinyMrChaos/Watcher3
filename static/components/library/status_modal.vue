<template>
<div id="movie_status">
    <div class="row at-row">
            <img class='poster col-sm-5 col-xs-24' :src="'/posters/' + (movie.poster || 'missing_poster.jpg')"/>
            <div class="col-sm-13 col-xs-24">
                <div id="modal_tags" class='flex flex-middle flex-between'>
                    <at-tag v-if='movie.finished_file'>
                        File: {{movie.finished_file}}
                    </at-tag>
                    <a :href="'http://www.imdb.com/title/' + movie.imdbid" target='_blank'>
                        <at-tag>
                            <i class='icon icon-link'></i>
                            IMDB
                        </at-tag>
                    </a>
                    <a :href="'https://www.themoviedb.org/movie/' + movie.tmdbid" target='_blank'>
                        <at-tag>
                            <i class='icon icon-link'></i>
                            TheMovieDB
                        </at-tag>
                    </a>
                    <at-tag>Date Added: {{movie.added_date}}</at-tag>
                    <at-tag>Source: {{movie.origin}}</at-tag>
                    <at-tag>
                        <i class="mdi mdi-star"></i>
                        {{movie.score}}
                    </at-tag>
                    <at-tag>
                        Theatrical Release: {{movie.release_date}}
                    </at-tag>
                    <at-tag>Home Release: {{movie.media_release_date || 'Unknown'}}</at-tag>
                </div>
                <p class="plot">{{movie.plot}}</p>
            </div>
            <div id="actions" class='row at-row col-sm-6 col-xs-24' style='text-align: center'>
                <div class='col-sm-24 col-xs-24'>
                    <at-button-group class='large_icons'>
                        <at-button icon="icon-search" title="Search"></at-button>
                        <at-button icon="icon-tag" title="Copy"></at-button>
                        <at-button icon="icon-trash-2" title="Download"></at-button>
                    </at-button-group>
                </div>
                <br/>
                <div class='movie_settings'>
                    <div class='col-sm-24 col-xs-12'>
                        Quality
                        {{movie.quality}}
                        <at-select v-model="movie.quality" style="width:100px;" size='large'>
                            <at-option v-for="q in qualities" v-bind:key="q" value='Default' >{{q}}</at-option>
                        </at-select>
                    </div>

                    <div class='col-sm-24 col-xs-12'>
                        Management
                        <at-select :value="management[movie.status]" style="width:100px;" size='large'>
                            <at-option value="Automatic">Automatic</at-option>
                            <at-option value="Disabled">Finished</at-option>
                        </at-select>
                    </div>

                    <div class='col-sm-24 col-xs-24'>
                        <at-button icon='icon-save' class='large_icons' type='success' style='width:75%' hollow></at-button>
                    </div>
                </div>
            </div>
    </div>
    <div id='search_results' class="row at-row">
        <template v-for="release in search_results">
            <div class="row at-row col-sm-24" :key="release.guid">
                <div class='col-sm-24'>
                    {{release.title}}
                </div>
                <div class='col-sm-12 col-xs-24'>
                    <ta
                    {{release.status}}
                </div>
                <div class='col-sm-12 col-xs-24'>
                    <at-button-group>
                        <at-button icon="icon-info" title="Info"></at-button>
                        <at-button icon="icon-download" title="Download"></at-button>
                        <at-button icon="icon-x" title="Mark Bad"></at-button>
                    </at-button-group>
                </div>
            </div>
        </template>
    </div>
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
                              }
        }
    },
    props: {
        movie: Object,
        qualities: Array,
        search_results: Array
    }
}

</script>


<style type="text/css">
.at-modal{
    max-height: calc(100% - 75px);
    max-width: 860px;
    overflow-y: scroll;
    top: 50px;
}
img.poster{
    height: 100%;
    width: 100%;
}
.large_icons i.icon{
    font-size: 16px;
}

p.plot{
    padding: 1em;
    font-size: 1.1em;
    text-indent: 1.5em;
}

#action_row{
    text-align: right;
}

#action_row > div{
    margin: 1em 0;
}
#modal_tags{
    padding: 0em 1em 1em 1em;
}

#modal_tags > *{
    margin: 2px 2px 2px 0;
}

.movie_settings{
    margin-top: 1em;
    width: 100%;
}

.movie_settings > div{
    margin-top: 1em;

}

#search_results{
    max-height: 18em;
    overflow-y: scroll;
    margin: 1em 1em 0 1em;
}

#search_results{
    padding: 0.5em;
}

#search_results > div:nth-child(even){
    background: rgba(0,0,0,.05)
}

</style>
