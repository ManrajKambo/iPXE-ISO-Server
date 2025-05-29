#!ipxe

dhcp

# Some menu defaults
set base-url {{ base_url }}
set menu-timeout 10000
set submenu-timeout ${menu-timeout}
isset ${menu-default} || set menu-default exit

# CPU detection
cpuid --ext 29 && set arch x64 || set arch x86
cpuid --ext 29 && set archb 64 || set archb 32
cpuid --ext 29 && set archl amd64 || set archl i386

### MAIN MENU ###
:start
menu iPXE Boot Menu
{{ menu_items }}
item --gap --   --- Advanced options ---
item --key c config Configure settings
item shell  Drop to iPXE shell
item reboot Reboot computer
item
item --key x exit   Exit iPXE and continue BIOS boot
choose --timeout ${menu-timeout} --default ${menu-default} selected || goto cancel
set menu-timeout 0
goto ${selected}

:cancel
echo You cancelled the menu, dropping you to a shell

:shell
echo Type 'exit' to get back to the menu
shell
set menu-timeout 0
set submenu-timeout 0
goto start

:failed
echo Booting failed, dropping to shell
goto shell

:reboot
reboot

:exit
exit

:config
config
goto start

:back
set submenu-timeout 0
clear submenu-default
goto start

### MAIN MENU ITEMS ###
{{ boot_sections }}