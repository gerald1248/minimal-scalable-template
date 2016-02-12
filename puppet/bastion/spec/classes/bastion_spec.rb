require 'spec_helper'

hiera_config = 'spec/fixtures/hiera/hiera.yaml'

describe 'bastion' do
  let(:hiera_config) { hiera_config }
  context 'on centos 7' do
    let(:facts) {{
      :auto_scaling_group1 => '0123456789',
      :auto_scaling_group2 => '9876543210',
      :elastic_load_balancer => '011235813',
    }}

    it { should compile.with_all_deps }
    context 'in class Init' do
      it { should contain_class('bastion') }
      it { should contain_class('bastion::install') }
    end
    context 'dependencies of class Install' do
      it { should contain_file('/etc/facter/facts.d').with_ensure('directory') }
      it { should contain_file('/etc/facter/facts.d/stack_ids.txt').with_ensure('file') }
    end
    context 'in class Install' do
      it { should contain_file('/home/ec2-user/scripts').with_ensure('directory') }
      it { should contain_file('/home/ec2-user/scripts/deploy.py').with_ensure('file').with_owner('ec2-user').with_mode('0644').with_source('puppet:///modules/bastion/deploy.py') }
      it { should contain_file('/home/ec2-user/stack_ids.json').with_ensure('file').with_owner('ec2-user').with_mode('0644') }
    end
  end
end
