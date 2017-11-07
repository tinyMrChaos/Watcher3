<template>
<div id="navbar">

<el-menu :default-active="current_page" mode="horizontal" @select="page_change">
    <img src='/static/images/logo.png' class='logo'/>
    <el-submenu index="1">
        <template slot="title">Library</template>
        <el-menu-item index="1-1">
            <i class="mdi mdi-movie"></i>
            Status
        </el-menu-item>
        <el-menu-item index="1-2">
            <i class="mdi mdi-plus-box"></i>
            Add
        </el-menu-item>
        <el-menu-item index="1-3">
            <i class="mdi mdi-briefcase"></i>
            Manage
        </el-menu-item>
    </el-submenu>
    <el-submenu index="2">
        <template slot="title">Settings</template>
        <el-menu-item index="2-1">Server</el-menu-item>
        <el-menu-item index="2-2">Search</el-menu-item>
    </el-submenu>
</el-menu>
</div>
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

div#navbar i{
    font-size: 1.25em;
}

img.logo{
    float: left;
    outline: none;
}

</style>
