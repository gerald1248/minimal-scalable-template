require 'spec_helper'

hiera_config = 'spec/fixtures/hiera/hiera.yaml'

describe 'application' do
  let(:hiera_config) { hiera_config }
  context 'on centos 7' do
    it { should compile.with_all_deps }
    context 'in class Init' do
      it { should contain_class('application') }
      it { should contain_class('application::install') }
    end
    context 'in class Install' do
      it { should contain_file('/var/www/html/index.html').with_ensure('file').with_mode('0755') }
      it { should contain_file('/var/www/html/js').with_ensure('directory') }
      it { should contain_file('/var/www/html/js/main.js').with_ensure('file') }
    end
  end
end
