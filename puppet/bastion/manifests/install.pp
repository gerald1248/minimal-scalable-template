# Class: bastion::install
#
class bastion::install {
  file { '/etc/facter/facts.d':
    ensure => directory,
  } ->
  file { '/etc/facter/facts.d/stack_ids.txt':
    ensure => file,
  } ->
  file { '/home/ec2-user/scripts':
    ensure => directory,
  } ->
  file { '/home/ec2-user/scripts/deploy.sh':
    ensure  => file,
    owner   => 'ec2-user',
    mode    => '0744',
    content => template('bastion/deploy.sh.erb'),
  }
}
