cmake_minimum_required (VERSION 2.8)

project (kombi NONE)
set (CMAKE_INSTALL_MESSAGE LAZY)

install (DIRECTORY data src/lib DESTINATION "${CMAKE_INSTALL_PREFIX}"
  PATTERN "*.pyc" EXCLUDE
  PATTERN "__pycache__" EXCLUDE
  PERMISSIONS
    OWNER_READ
    GROUP_READ
    WORLD_READ
    WORLD_EXECUTE
)

# posix executables
file(COPY src/bin/kombi DESTINATION ${CMAKE_INSTALL_PREFIX}/bin
  FILE_PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ
  GROUP_EXECUTE WORLD_READ WORLD_EXECUTE
)

file(COPY src/bin/kombi-gui DESTINATION ${CMAKE_INSTALL_PREFIX}/bin
  FILE_PERMISSIONS OWNER_READ OWNER_WRITE OWNER_EXECUTE GROUP_READ
  GROUP_EXECUTE WORLD_READ WORLD_EXECUTE
)

# windows executables
file(COPY src/bin/kombi.bat DESTINATION ${CMAKE_INSTALL_PREFIX}/bin)
file(COPY src/bin/kombi-gui.bat DESTINATION ${CMAKE_INSTALL_PREFIX}/bin)

install(FILES info.json DESTINATION "${CMAKE_INSTALL_PREFIX}")
