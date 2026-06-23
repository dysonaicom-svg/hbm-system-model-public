// Verilated -*- C++ -*-
// DESCRIPTION: Verilator output: Model implementation (design independent parts)

#include "Vhbm_controller_tb_simple__pch.h"

//============================================================
// Constructors

Vhbm_controller_tb_simple::Vhbm_controller_tb_simple(VerilatedContext* _vcontextp__, const char* _vcname__)
    : VerilatedModel{*_vcontextp__}
    , vlSymsp{new Vhbm_controller_tb_simple__Syms(contextp(), _vcname__, this)}
    , rootp{&(vlSymsp->TOP)}
{
    // Register model with the context
    contextp()->addModel(this);
}

Vhbm_controller_tb_simple::Vhbm_controller_tb_simple(const char* _vcname__)
    : Vhbm_controller_tb_simple(Verilated::threadContextp(), _vcname__)
{
}

//============================================================
// Destructor

Vhbm_controller_tb_simple::~Vhbm_controller_tb_simple() {
    delete vlSymsp;
}

//============================================================
// Evaluation function

#ifdef VL_DEBUG
void Vhbm_controller_tb_simple___024root___eval_debug_assertions(Vhbm_controller_tb_simple___024root* vlSelf);
#endif  // VL_DEBUG
void Vhbm_controller_tb_simple___024root___eval_static(Vhbm_controller_tb_simple___024root* vlSelf);
void Vhbm_controller_tb_simple___024root___eval_initial(Vhbm_controller_tb_simple___024root* vlSelf);
void Vhbm_controller_tb_simple___024root___eval_settle(Vhbm_controller_tb_simple___024root* vlSelf);
void Vhbm_controller_tb_simple___024root___eval(Vhbm_controller_tb_simple___024root* vlSelf);

void Vhbm_controller_tb_simple::eval_step() {
    VL_DEBUG_IF(VL_DBG_MSGF("+++++TOP Evaluate Vhbm_controller_tb_simple::eval_step\n"); );
#ifdef VL_DEBUG
    // Debug assertions
    Vhbm_controller_tb_simple___024root___eval_debug_assertions(&(vlSymsp->TOP));
#endif  // VL_DEBUG
    vlSymsp->__Vm_deleter.deleteAll();
    if (VL_UNLIKELY(!vlSymsp->__Vm_didInit)) {
        vlSymsp->__Vm_didInit = true;
        VL_DEBUG_IF(VL_DBG_MSGF("+ Initial\n"););
        Vhbm_controller_tb_simple___024root___eval_static(&(vlSymsp->TOP));
        Vhbm_controller_tb_simple___024root___eval_initial(&(vlSymsp->TOP));
        Vhbm_controller_tb_simple___024root___eval_settle(&(vlSymsp->TOP));
    }
    VL_DEBUG_IF(VL_DBG_MSGF("+ Eval\n"););
    Vhbm_controller_tb_simple___024root___eval(&(vlSymsp->TOP));
    // Evaluate cleanup
    Verilated::endOfEval(vlSymsp->__Vm_evalMsgQp);
}

//============================================================
// Events and timing
bool Vhbm_controller_tb_simple::eventsPending() { return false; }

uint64_t Vhbm_controller_tb_simple::nextTimeSlot() {
    VL_FATAL_MT(__FILE__, __LINE__, "", "No delays in the design");
    return 0;
}

//============================================================
// Utilities

const char* Vhbm_controller_tb_simple::name() const {
    return vlSymsp->name();
}

//============================================================
// Invoke final blocks

void Vhbm_controller_tb_simple___024root___eval_final(Vhbm_controller_tb_simple___024root* vlSelf);

VL_ATTR_COLD void Vhbm_controller_tb_simple::final() {
    Vhbm_controller_tb_simple___024root___eval_final(&(vlSymsp->TOP));
}

//============================================================
// Implementations of abstract methods from VerilatedModel

const char* Vhbm_controller_tb_simple::hierName() const { return vlSymsp->name(); }
const char* Vhbm_controller_tb_simple::modelName() const { return "Vhbm_controller_tb_simple"; }
unsigned Vhbm_controller_tb_simple::threads() const { return 1; }
void Vhbm_controller_tb_simple::prepareClone() const { contextp()->prepareClone(); }
void Vhbm_controller_tb_simple::atClone() const {
    contextp()->threadPoolpOnClone();
}
