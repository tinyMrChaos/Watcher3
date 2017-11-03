<template>
<div id="navbar">
    <at-menu mode="horizontal" v-on:on-select="page_change" :active-Name="current_page">
        <!-- <img src='/static/images/logo.png' style="float:left"/> -->
        <at-submenu>
            <template slot="title">
                Library
            </template>
            <at-menu-item name="1-1">
                <i class="mdi mdi-movie"></i>
                Movies
            </at-menu-item>
            <at-menu-item name="1-2">
                <i class="icon icon-plus-square"></i>
                Add
            </at-menu-item>
            <at-menu-item name="1-3">
                <i class="icon icon-briefcase"></i>
                Manage
            </at-menu-item>
        </at-submenu>
        <at-submenu>
            <template slot="title">

                Settings
            </template>
            <at-menu-item name="2-2">
                <i class="icon icon-server"></i>
                Server
            </at-menu-item>
            <at-menu-item name="2-2">
                <i class="icon icon-search"></i>
                Search
            </at-menu-item>
            <at-menu-item name="2-3">Manage</at-menu-item>
        </at-submenu>
    </at-menu>
</template>


<script>

pages = {"1-1": "/library/status",
         "1-2": "/library/add"
         }

module.exports = {
    data(){
        var p = this.$parent.$route.path;
        return {current_page: Object.keys(pages).filter(function(key) {return pages[key] === p})[0]
                }
    },
    methods: {
        page_change: function(index){
            this.$parent.$router.push(pages[index])
        },
    }
}

</script>


<style type="text/css">
div#navbar{
    position: fixed;
    width: 100%;
    top: 0;
    z-index: 1000;
    max-width: 960px;
    margin: 0 auto;
}

#navbar i{
    font-size: 1.25em;
}

</style>
