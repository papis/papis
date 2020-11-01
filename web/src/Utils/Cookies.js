"use strict"

exports.setCookies = c => () => { document.cookie = c; return {} }
exports.getCookies = () => document.cookie
