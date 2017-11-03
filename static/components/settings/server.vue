<template>
<div id="server">
    THIS IS A TEST<br/>
    Hello {{name}}
    <br/>
    <b v-on:click="get_movies(1)">Get Movies</b>
    <b v-on:click="print_movies()">Print Movies</b>

</div>
</template>


<script>
module.exports = {
    data(){
        return {name: 'world',
                movies: this.retm()
                }
    },
    methods: {
        get_movies: function(page){
            this.movies = {'movie': 'new movie'}
        },
        print_movies: function(){
            console.log(this.movies)
        },
        retm: function(){
            return 'M'
        }

    }

}

</script>
