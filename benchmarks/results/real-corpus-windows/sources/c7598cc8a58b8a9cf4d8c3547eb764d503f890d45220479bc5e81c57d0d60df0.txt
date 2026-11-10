#include "AutoReservationV3.hpp"
#include "Compare.hpp"
#include "../reservation/Data.hpp"
#include <iostream>
namespace {
void require(bool condition,const char* message){if(!condition)throw std::runtime_error(message);}
void arithmetic() {
    using namespace AutoReserveV3;
    const auto maximum=(std::numeric_limits<size_t>::max)();
    for(auto goal:{Goal::Speed,Goal::Memory})for(size_t limit:{size_t{1},size_t{1000},maximum/sizeof(Token),maximum})
        for(size_t cap:{size_t{0},limit/2,limit-1})for(size_t budget:{size_t{0},size_t{1},size_t{1048576},maximum})
            for(bool mature:{false,true})for(bool pressure:{false,true})
                for(double prediction:{0.0,100.0,static_cast<double>(limit),(std::numeric_limits<double>::infinity)()}) {
                    const auto h=choose(goal,cap,limit,mature,pressure,100,false,prediction,budget);
                    require(h.request>cap && h.request<=limit,"V3 progress/overflow failure");
                    require(h.lower<=h.effectiveUpper && h.effectiveUpper<=limit,"V3 invalid window");
                    if(!h.floorOverride)require(h.request<=h.byteUpper,"V3 byte ceiling exceeded silently");
                    else require(h.lower>h.byteUpper && h.request<=h.lower,"V3 floor override invalid");
                    if(h.tailApplied)require(h.request==h.tailBound,"V3 remaining-byte bound mismatch");
                    else require(h.request>=h.lower,"V3 lost geometric progress");
                }
    for(size_t q:{size_t{6},size_t{7},size_t{8}}) {
        for(size_t cap=0;cap<1024;++cap)
            require(pressureFloor(cap,maximum,q)==cap+(std::max)(cap*(q-4)/4,size_t{1}),"Incorrect rational floor");
        require(pressureFloor(maximum-1,maximum,q)==maximum,"Pressure floor must saturate");
    }
    const auto unpressured=choose(Goal::Memory,1000,maximum,true,false,100000,false,0,1048576);
    const auto pressured=choose(Goal::Memory,1000,maximum,true,true,100000,false,0,1048576);
    require(unpressured.lower==1250 && pressured.lower==1000*AUTO_V3_MEMORY_QUARTERS/4,"Pressure must be the only trigger");
    for(size_t n=1;n<1024;++n)for(size_t moved=0;moved<n*5;++moved) {
        require(copyPressure(Goal::Speed,moved,n,true)==(moved+n>n*1.5),"Projected speed pressure mismatch");
        require(copyPressure(Goal::Memory,moved,n,true)==(moved+n>n*3),"Projected memory pressure mismatch");
    }
    require(copyPressure(Goal::Speed,maximum,maximum,true),"Projected speed large counter");
    require(!copyPressure(Goal::Memory,maximum,maximum,true),"Projected pressure overflow");
    const auto tail=remainingBound(65535,2,false,maximum);
    require(tail.fits && tail.count==65538,"Dense near-end bound incorrect");
    require(!remainingBound(maximum,1,false,maximum).fits,"Tail bound overflow");
    const auto h=choose(Goal::Memory,65534,maximum,true,false,2,false,65538,524288);
    require(h.tailApplied && h.request==65538,"Near-end growth must fit all remaining tokens");
}
}
int main(int argc,char** argv){
    try {
        arithmetic();AutoCheck::selfTest();
        if(argc==2 && std::string_view(argv[1])=="--self-test"){std::cout<<"V3 budget/tail arithmetic passed\n";return 0;}
        if(argc<2)throw std::invalid_argument("Usage: AutoV3Verify INPUT... | --self-test");
        for(int i=1;i<argc;++i)require(AutoCheck::compare(MatrixData::read(argv[i])),"Expected valid V3 fixture");
        std::cout<<"V3 exact token/value/diagnostic comparison passed\n";
    }catch(const std::exception& ex){std::cerr<<ex.what()<<'\n';return 1;}
}
