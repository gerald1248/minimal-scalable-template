"use strict";

var App = function() {
  this.states = [
    "* * *\n     \n* S *\n     \n* O *\n     \n* D *\n     \n* A *\n     \n* * *",
    " * * \n*   *\n  S  \n*   *\n  O  \n*   *\n  D  \n*   *\n  A  \n*   *\n *** "
  ];
  this.interval = 500;
  this.refresh(0);
}

App.prototype.refresh = function(i) {
  var self = this;
  i %= 2;
  document.getElementById("preform").innerHTML = this.states[i];
  setTimeout(function() { self.refresh(i + 1); }, this.interval); 
}

function init() {
  var app = new App; 
}

window.onload = init;
