# Class: application::install 
#
class application::install {
  file { '/var/www/html/index.html':
    ensure => file,
    mode   => '0755',
    source => 'puppet:///modules/application/docroot/index.html',
  } ->
  file { '/var/www/html/js':
    ensure => directory,
  } ->
  file { '/var/www/html/js/main.js':
    ensure => file,
    source => 'puppet:///modules/application/docroot/js/main.js',
  }
}
