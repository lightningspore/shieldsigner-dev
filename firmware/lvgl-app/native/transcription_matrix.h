#pragma once
#include <nlohmann/json.hpp>
#include <vector>
#include <stdexcept>
#include <string>
// Pinned LVGL qrcodegen layout: size byte, then row-major LSB-first modules.
// This small matrix is supplied by the ORIGINAL Python QR library, preserving
// its segmentation/mask for hand transcription. Never log this secret data.
static std::vector<uint8_t> transcription_matrix(const nlohmann::json &cfg){
 if(!cfg.contains("matrix_hex"))return {};
 auto hex=cfg.at("matrix_hex").get<std::string>();
 if(hex.size()<2||hex.size()>276||hex.size()%2)throw std::runtime_error("Invalid transcription matrix length");
 std::vector<uint8_t> bytes(hex.size()/2);
 auto nibble=[](char c)->uint8_t{if(c>='0'&&c<='9')return c-'0';if(c>='a'&&c<='f')return c-'a'+10;throw std::runtime_error("Invalid transcription matrix encoding");};
 for(size_t i=0;i<bytes.size();++i)bytes[i]=(nibble(hex[2*i])<<4)|nibble(hex[2*i+1]);
 int n=bytes[0];
 if((n!=21&&n!=25&&n!=29&&n!=33)||bytes.size()!=size_t(1+(n*n+7)/8)||cfg.at("num_modules").get<int>()!=n)throw std::runtime_error("Transcription matrix/template mismatch");
 return bytes;
}
