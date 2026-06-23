// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Symbol table implementation internals

#include "Vhbm_controller_tb_simple__pch.h"
#include "Vhbm_controller_tb_simple.h"
#include "Vhbm_controller_tb_simple___024root.h"
#include "Vhbm_controller_tb_simple___024unit.h"

// FUNCTIONS
Vhbm_controller_tb_simple__Syms::~Vhbm_controller_tb_simple__Syms()
{
}

Vhbm_controller_tb_simple__Syms::Vhbm_controller_tb_simple__Syms(VerilatedContext* contextp, const char* namep, Vhbm_controller_tb_simple* modelp)
    : VerilatedSyms{contextp}
    // Setup internal state of the Syms class
    , __Vm_modelp{modelp}
    // Setup module instances
    , TOP{this, namep}
{
        // Check resources
        Verilated::stackCheck(302);
    // Configure time unit / time precision
    _vm_contextp__->timeunit(-9);
    _vm_contextp__->timeprecision(-12);
    // Setup each module's pointers to their submodules
    // Setup each module's pointer back to symbol table (for public functions)
    TOP.__Vconfigure(true);
}
