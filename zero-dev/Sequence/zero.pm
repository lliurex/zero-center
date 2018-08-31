#!/usr/bin/perl
use warnings;
use strict;
use Debian::Debhelper::Dh_Lib;

my $count = 0;
my $pkexec_counter = 0;
my $zero_counter = 0;
my $found = 0;
foreach my $item (@{$dh{WITH}}){
        if ($item =~ /pkexec/){
                $pkexec_counter = $count;
                $found = 1;
        }   
        if ($item =~ /zero/){
                $zero_counter = $count;
        }   
        $count++;
}

if ($found and ($pkexec_counter < $zero_counter)){
        insert_before('dh_pkexec','dh_zeroinstaller');
}
else{
        insert_after('dh_install','dh_zeroinstaller');
        if(not $found){
		insert_after('dh_zeroinstaller','dh_pkexec');
        }   
}
1;
