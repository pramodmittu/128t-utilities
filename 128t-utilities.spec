# Specfile for packaging utilities for 128T AMIs

%define major 3
%define minor 5
%define patch 6

# workaround to force RPM to ignore the pyo and pyc files it generates during rpmbuild.
%global __os_install_post \
    /usr/lib/rpm/redhat/brp-compress \
    %{!?_debug_package:/usr/lib/rpm/redhat/brp-strip %{_strip}} \
    /usr/lib/rpm/redhat/brp-strip-static-archive %{__strip} \
    /usr/lib/rpm/redhat/brp-strip-comment-note %{_strip} %{_objdump} \
    /usr/lib/rpm/redhat/brp-java-repack-jars

Name:           128t-utilities
Summary:        Utilites for 128T AMIs
License:        private
Version:        %{major}.%{minor}.%{patch}
Source0:        %{name}.tar.gz
Release:        %{?_releasenumber:%{_releasenumber}%{?dist}}%{!?_releasenumber:0.unofficial}
Buildroot:      %{_tmppath}/%{name}-%{version}-%{release}-root
Requires:       datadog-agent, expect, 128t-utilities-pip

%description
Provides all utilities required to run 128T instances in the cloud

%package        pip
Summary:        TTC python utilities
Requires:       python3
BuildRequires:  python3-devel

%description    pip
This package contains the Python pip files to expose functionality outsidde 128T instances

%prep
%setup -q -n %{name}

%build
env CFLAGS="$RPM_OPT_FLAGS" %{__python3} setup.py build

%install
mkdir -p $RPM_BUILD_ROOT%{_pindrop_etc}/128t/
mkdir -p $RPM_BUILD_ROOT%{_pindrop_bin}/
mkdir -p $RPM_BUILD_ROOT%{_pindrop_lib}/
mkdir -p $RPM_BUILD_ROOT/etc/systemd/system/
mkdir -p $RPM_BUILD_ROOT/etc/dd-agent/conf.d/
mkdir -p $RPM_BUILD_ROOT/etc/datadog-agent/conf.d/
mkdir -p $RPM_BUILD_ROOT/etc/pki/128technology/
mkdir -p $RPM_BUILD_ROOT/etc/sysctl.d/
mkdir -p $RPM_BUILD_ROOT/var/log/128t_alarms/

mkdir -p $RPM_BUILD_ROOT/etc/salt/pki/minion/
mkdir -p $RPM_BUILD_ROOT/etc/128technology/salt/pki/master/
mkdir -p $RPM_BUILD_ROOT/root/.ssh/

%{__python3} setup.py install \
    --root=$RPM_BUILD_ROOT \
    --record=INSTALLED_FILES \
    --install-lib=%{_pindrop_lib} \
    --install-scripts=%{_pindrop_bin}

cp conf/*.json $RPM_BUILD_ROOT%{_pindrop_etc}/128t/

# 128T license
cp conf/release.pem $RPM_BUILD_ROOT/etc/pki/128technology/

# enable reboot on panic
# there's a bug in 128t/DPDK that causes panic on module unload / uio_release sometimes
cp conf/98-panic.conf $RPM_BUILD_ROOT/etc/sysctl.d/

cp -R dd-agent/* $RPM_BUILD_ROOT/etc/dd-agent/
cp -fR datadog-agent/* $RPM_BUILD_ROOT/etc/datadog-agent/
cp systemd/*.service $RPM_BUILD_ROOT/etc/systemd/system/
cp systemd/*.timer $RPM_BUILD_ROOT/etc/systemd/system/
cp src/*.sh $RPM_BUILD_ROOT%{_pindrop_bin}/
cp src/*.py $RPM_BUILD_ROOT%{_pindrop_bin}/

cp salt_keys/minion* $RPM_BUILD_ROOT/etc/salt/pki/minion/
cp salt_keys/master* $RPM_BUILD_ROOT/etc/128technology/salt/pki/master/
cp salt_keys/t128_id_rsa $RPM_BUILD_ROOT/root/.ssh/

%preun
if [ $1 -eq 0 ]; then # uninstall
    systemctl disable --now datadog-agent.service
    systemctl disable --now export-128t-config.timer
    systemctl disable --now import-128t-config.service
    systemctl disable --now initialize-instance.service
    systemctl disable --now is-conductor.service
    systemctl disable --now check-128t-service.timer
    systemctl disable --now check-ttc-receivers.timer
fi

%post
if [ $1 -eq 2 ]; then # upgrade
    systemctl disable datadog-agent.service
    systemctl disable export-128t-config.timer
    systemctl disable import-128t-config.service
    systemctl disable initialize-instance.service
    systemctl disable is-conductor.service
    systemctl disable check-128t-service.timer
    systemctl disable check-ttc-receivers.timer
fi

systemctl reenable datadog-agent.service
systemctl enable export-128t-config.timer
systemctl enable import-128t-config.service
systemctl enable initialize-instance.service
systemctl enable is-conductor.service
systemctl enable check-128t-service.timer
systemctl enable check-ttc-receivers.timer

# Must allow memory management by cgroup to be enabled
# https://github.com/DataDog/docker-dd-agent#cgroups
sed -i 's|\(GRUB_CMDLINE_LINUX_DEFAULT=".*\)"|\1 cgroup_enable=memory swapaccount=1"|' /etc/default/grub
if [[ -n $(which update-grub) ]]; then
    update-grub
elif [[ -n $(which grub2-mkconfig) ]]; then
    grub2-mkconfig > /boot/grub2/grub.cfg
fi

%files
%dir %attr(755, root, root) /opt/pindrop/
%attr(755, root, root) %{_pindrop_bin}/configure-dd-agent.sh
%attr(755, root, root) %{_pindrop_bin}/configure-datadog-agent.sh
%attr(755, root, root) %{_pindrop_bin}/export_128t_config.sh
%attr(755, root, root) %{_pindrop_bin}/import_128t_config.sh
%attr(755, root, root) %{_pindrop_bin}/is_conductor.sh
%attr(755, root, root) %{_pindrop_bin}/check_128t.py
%attr(755, root, root) %{_pindrop_bin}/service_check_reporter.py
%attr(755, root, root) %{_pindrop_bin}/remove_rpms.sh
%attr(755, root, root) %{_pindrop_bin}/check_receivers_state.sh

/etc/systemd/system/datadog-agent.service
/etc/systemd/system/datadog-agent-process.service
/etc/systemd/system/datadog-agent-trace.service
/etc/systemd/system/export-128t-config.service
/etc/systemd/system/export-128t-config.timer
/etc/systemd/system/import-128t-config.service
/etc/systemd/system/initialize-instance.service
/etc/systemd/system/is-conductor.service
/etc/systemd/system/check-128t-service.service
/etc/systemd/system/check-128t-service.timer
/etc/systemd/system/check-ttc-receivers.service
/etc/systemd/system/check-ttc-receivers.timer

/etc/dd-agent/datadog.conf
/etc/dd-agent/conf.d/disk.yaml
