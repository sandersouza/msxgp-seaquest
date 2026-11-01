# Only the temporary copy supplied by play.py is modified.
set power off
if {[catch {
    diskmanipulator import diska $::env(SEAQUEST_RUN_COM) $::env(SEAQUEST_RUN_AUTOEXEC)
} error]} {
    puts stderr "Cannot prepare temporary DOS disk: $error"
    exit 1
}
set power on
