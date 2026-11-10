#include "Token.hpp"
#include "BenchmarkUtils.hpp"
#include <charconv>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string_view>

namespace {
struct Growth { size_t count, request, capacity; };
struct Plan { size_t count, initial; std::vector<Growth> growths; };
struct Observed { size_t moved=0, capacity=0, expansions=0; };
size_t number(std::string_view text) {
    size_t n=0;
    const auto r=std::from_chars(text.data(),text.data()+text.size(),n);
    if(text.empty() || r.ec!=std::errc{} || r.ptr!=text.data()+text.size())
        throw std::invalid_argument("Invalid unsigned count");
    return n;
}
void validate(const Plan& p) {
    const size_t limit=std::vector<Token>().max_size();
    if(!p.count || p.count>limit || p.initial>limit)throw std::invalid_argument("Invalid token capacity");
    size_t cap=p.initial;
    for(const auto& g:p.growths) {
        if(g.count!=cap || g.count>=p.count || g.request<=cap || g.request>limit || g.capacity!=g.request)
            throw std::invalid_argument("Invalid or unsupported growth schedule");
        cap=g.capacity;
    }
    if(cap<p.count)throw std::invalid_argument("Incomplete growth schedule");
}
// Replay the recorded vector schedule; no density prediction, lexer, source or DOM.
std::uint64_t replay(const Plan& p,Observed* observed=nullptr) {
    std::vector<Token> tokens;
    tokens.reserve(p.initial);
    size_t event=0,moved=0;
    for(size_t i=0;i<p.count;++i) {
        if(tokens.size()==tokens.capacity()) {
            const auto& g=p.growths.at(event++);
            if(g.count!=tokens.size())throw std::runtime_error("Replay diverged");
            moved+=tokens.size();
            tokens.reserve(g.request);
            if(tokens.capacity()!=g.capacity)throw std::runtime_error("Allocator capacity differs from recorded schedule");
        }
        tokens.push_back({Parser::TokenType::Number,i,1,i+1,i,1});
    }
    if(event!=p.growths.size())throw std::runtime_error("Unused replay event");
    BenchmarkUtils::escape(&tokens);
    if(observed)*observed={moved,tokens.capacity(),event};
    return tokens.back().position+tokens.front().length;
}
void selfTest() {
    Plan p{9,2,{{2,4,4},{4,8,8},{8,9,9}}};validate(p);
    Observed o;
    if(replay(p,&o)!=9 || o.moved!=14 || o.capacity!=9 || o.expansions!=3)
        throw std::runtime_error("Replay accounting mismatch");
    Plan exact{9,9,{}};validate(exact);replay(exact,&o);
    if(o.moved || o.expansions || o.capacity!=9)throw std::runtime_error("Exact plan grew");
    for(const auto& bad:std::vector<Plan>{{9,2,{}},{9,2,{{3,9,9}}},{9,2,{{2,2,2}}},{9,2,{{2,9,10}}},{0,0,{}}}) {
        bool rejected=false;try{validate(bad);}catch(const std::invalid_argument&){rejected=true;}
        if(!rejected)throw std::runtime_error("Invalid schedule accepted");
    }
    for(auto bad:{"-1","1x","184467440737095516160"}) {
        bool rejected=false;try{number(bad);}catch(const std::invalid_argument&){rejected=true;}
        if(!rejected)throw std::runtime_error("Invalid count accepted");
    }
}
}
int main(int argc,char** argv) {
    try {
        if(argc==2 && std::string_view(argv[1])=="--self-test") {
            selfTest();std::cout<<"Replay accounting and rejected schedules passed\n";return 0;
        }
        if(argc!=6)throw std::invalid_argument("Usage: TokenRelocation TOKENS INITIAL PLAN ITERATIONS SAMPLES");
        Plan p{number(argv[1]),number(argv[2]),{}};
        std::ifstream input(argv[3]);if(!input)throw std::runtime_error("Cannot open replay plan");
        std::string count,request,capacity;
        while(input>>count) {
            if(!(input>>request>>capacity))throw std::invalid_argument("Truncated schedule");
            p.growths.push_back({number(count),number(request),number(capacity)});
        }
        const size_t iterations=number(argv[4]),samples=number(argv[5]);
        if(!iterations || iterations>1000 || !samples || samples>101)throw std::invalid_argument("Invalid measurement count");
        validate(p);Observed observed;replay(p,&observed);
        const auto t=BenchmarkUtils::measure([&]{return replay(p);},iterations,samples);
        std::cout<<std::setprecision(12)
            <<"tokens,initial_capacity,final_capacity,expansions,moved_tokens,token_size,iterations,samples,median_us,min_us,max_us,configuration\n"
            <<p.count<<','<<p.initial<<','<<observed.capacity<<','<<observed.expansions<<','<<observed.moved<<','<<sizeof(Token)<<','
            <<iterations<<','<<samples<<','<<t.medianUs<<','<<t.minUs<<','<<t.maxUs<<','<<DIAG_CONFIGURATION<<'\n';
    }catch(const std::exception& ex){std::cerr<<ex.what()<<'\n';return 1;}
}
