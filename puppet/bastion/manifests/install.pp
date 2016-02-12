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
  file { '/home/ec2-user/stack_ids.json':
    ensure  => file,
    owner   => 'ec2-user',
    mode    => '0644',
    content => template('bastion/stack_ids.json.erb'),
  } ->
  file { '/home/ec2-user/scripts/deploy.py':
    ensure => file,
    owner  => 'ec2-user',
    mode   => '0644',
    source => 'puppet:///modules/bastion/deploy.py',
  }
}
